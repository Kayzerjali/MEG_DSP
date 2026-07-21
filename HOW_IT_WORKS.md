# How it works — modifying and reusing this code

This document is for when you want to do more than run the program: change it, add your own
filter, or lift a piece of it into your own script.

It assumes you can run the program already (see [README.md](README.md)) and that you know
roughly what a Python class is. It does not assume anything beyond that.

**If you only want to borrow one piece of this code for your own project**, skip straight to
[section 7](#7-borrowing-one-piece-for-your-own-script). You don't need to understand the rest.

---

## 1. The files

Six Python files, each with one job.

| File | Job |
|---|---|
| `dsp.py` | **Start here.** The entry point — the file you run. It's a list of everything the program should use, then a `run()` call. |
| `DataSource.py` | Where the numbers come from. The real hardware (`NIDAQ`) and a fake signal generator (`MockSignal`). |
| `Filter.py` | Everything that modifies the signal: bandpass, notch, and the PCA family. Plus `FilterManager`, which chains them. |
| `Display.py` | Everything that draws: the three graph types, plus `DisplayManager`, which arranges them. |
| `Shell.py` | The `dsp:` command prompt. One method per command. |
| `Container.py` | The wiring. Keeps track of every object so the shell can reach in and change things while the program runs. |

A useful pattern to notice: `Filter.py` and `Display.py` each contain **several small classes
that do the work, plus one "Manager" class that owns them**. When you add something new,
you're writing one more small class and registering it.

---

## 2. How data flows

```
   DataSource                 FilterManager                DisplayManager
  ┌────────────┐            ┌───────────────┐            ┌──────────────┐
  │  NIDAQ or  │  chunks of │ applies each  │  (raw,     │  six graphs, │
  │ MockSignal │ ─────────► │ active filter │ ─ filtered)│  redrawn 20  │
  │            │  numbers   │ in sequence   │  ───────►  │  times/sec   │
  └────────────┘            └───────────────┘            └──────────────┘
                                    ▲
                                    │ add/remove filters while running
                                    │
                              ┌───────────┐
                              │ dsp:      │  ◄── you, typing
                              │ Shell.py  │
                              └───────────┘
```

The data moves in **chunks**, not one reading at a time — 100 samples per channel per chunk
by default. Everything is built around Python generators, which are functions that hand back
one chunk each time they're asked, instead of computing everything up front. That's what
lets the program run forever on a live stream.

The key detail is that **`FilterManager` passes along a pair: `(raw, filtered)`**. Both the
untouched and the processed signal travel together all the way to the display. That's how the
top row of graphs can show raw data and the bottom row filtered data at the same instant.

`DisplayManager` splits its list of graphs in half: **the first half gets the raw signal, the
second half gets the filtered signal.** That's why `dsp.py` registers exactly six displays,
three "Raw" then three "Filtered". If you register an odd number, or list them out of order,
the split lands in the wrong place.

---

## 3. The one rule you must not break

**Signal data is always a 2D numpy array shaped `(number_of_channels, number_of_samples)`.**

Channels are rows, time runs left to right along the columns. With 2 sensors and 100 samples:

```python
data.shape   # (2, 100)
data[0]      # all 100 readings from sensor 1
data[1]      # all 100 readings from sensor 2
data[:, 0]   # both sensors' first reading
```

Every filter takes this shape in and must give the same shape back. Every display expects it.
If you write a filter that returns something else, you'll get a confusing error somewhere far
away in the drawing code.

Watch out for one trap: **scikit-learn wants the opposite layout**, `(samples, channels)`. So
every PCA filter in `Filter.py` transposes on the way in and back again on the way out:

```python
data_t = np.array(data).T        # (channels, samples) -> (samples, channels), for sklearn
components = self.pca.fit_transform(data_t)
...
return data_filt.T               # and back again, so the pipeline stays consistent
```

If you write a filter using any other sklearn tool, you need those two `.T`s.

---

## 4. The container, in plain terms

`Container.py` is the part most likely to look mysterious, so here's what it's for.

The problem it solves: the `dsp:` prompt needs to reach the *exact same* bandpass filter
object that's currently processing data, so that `bp_filt 1 100 4` retunes the live one rather
than some unrelated copy. The container is just a dictionary that keeps track of those objects
so everyone can find them by name.

There are two stages, and the distinction matters:

- **Registering** — "here's how to build a bandpass filter, file it under the name `bp`." No
  object is created yet; you're storing a recipe.
- **Resolving** — "actually build the `bp` one now, and remember the result." This creates the
  object and stores it so it can be looked up later with `get_instance("bp")`.

This is why filters are registered at startup but only come into existence when you type
`add_filt bp`. Nothing is built until it's needed.

Three registration methods, and **using the right one matters**:

| Method | Use for | Why it's separate |
|---|---|---|
| `register(name, ...)` | Everything else | Plain storage. |
| `register_filter(name, ...)` | Filters | Also adds it to the list that `list_registered_filters` shows. Use anything else and your filter will be invisible to the CLI. |
| `register_display(title, ...)` | Displays | Also adds it to the list `DisplayManager` walks through to build the grid. |

**Display titles must be formatted `"Some Name : X Axis"`** — with spaces around the colon.
The `axis` command splits the title on `" : "` to rewrite the second half when you switch axes.
A title without that separator makes `axis` print `Error updating display: ...` and abandon the
retitling part way through, leaving some plots showing the old axis.

---

## 5. Adding your own filter

Three steps. Here's a complete, working example: a filter that multiplies the signal by a
number, useful for unit conversions.

**Step 1 — write the class** in `Filter.py`. It must inherit from `Filter` and implement
`process_chunk`:

```python
class Gain(Filter):
    """Multiplies the signal by a fixed factor."""

    def __init__(self, factor: float = 2.0):
        self.factor = factor

    def process_chunk(self, data):
        # data comes in as (num_channels, num_samples) -- and must go back out
        # the same shape. numpy multiplies element-by-element, so shape is preserved.
        return data * self.factor
```

**Step 2 — register it** in `dsp.py`, alongside the existing filters:

```python
container.register_filter("gain", lambda: Filter.Gain(factor=3.0))
```

The `lambda:` matters. You're handing over *instructions for building* the object, not the
object itself, so the container can delay creating it until it's needed.

**Step 3 — use it.** Restart the program and type `add_filt gain`. It'll also show up in
`list_registered_filters`.

### If your filter has state

The bandpass and notch filters are **stateful**: a proper digital filter needs to remember
where the previous chunk left off, or you get a click at every chunk boundary. That's what the
`self.zi` variable is — scipy's filter state, carried from one call of `process_chunk` to the
next.

If you write a stateful filter, and it can be reconfigured from the CLI while running, guard
the state with a `threading.Lock` exactly as `BandPass` does. **The command prompt runs on a
different thread from the data processing**, so without a lock you can change coefficients
halfway through a chunk and get garbage or a crash.

If your filter is stateless (like `Gain` above), you don't need a lock.

---

## 6. Adding your own data source

This is the most likely thing you'll want to change — for example, to replay data from a file
instead of reading live hardware.

Write a class that inherits from `DataSource` and provides two methods:

- **`data_stream(num_samples_per_read=100)`** — a generator that `yield`s arrays shaped
  `(num_channels, num_samples)`. Yield `None` if no data is ready right now; the pipeline
  handles that and simply doesn't redraw.
- **`close()`** — release whatever you opened. Called on shutdown.

In practice you should also provide `set_axis(axis)`, because the `axis` command calls it. It
can do nothing at all, but it must exist or `axis` will crash. `MockSignal.set_axis` is a
one-line example.

Here's a working CSV replayer. Assumes a file with one column per channel and one row per
time point:

```python
class CSVReplay(DataSource):
    """Replays data from a CSV file, one chunk at a time, as if it were live."""

    def __init__(self, filename: str, sample_rate: int = 1000):
        # (rows, channels) as stored -> transpose to our (channels, samples) convention
        self.data = np.loadtxt(filename, delimiter=",").T
        if self.data.ndim == 1:            # a single-column file loads as 1D
            self.data = self.data.reshape(1, -1)
        self.sample_rate = sample_rate
        self.position = 0

    def set_axis(self, axis: str):
        print(f"CSVReplay: axis '{axis}' ignored -- file data has no axes")

    def data_stream(self, num_samples_per_read: int = 100):
        while True:
            start = self.position
            end = start + num_samples_per_read

            if end > self.data.shape[1]:   # reached the end -- loop back to the start
                self.position = 0
                continue

            self.position = end
            yield self.data[:, start:end]
            time.sleep(num_samples_per_read / self.sample_rate)  # replay at realistic speed

    def close(self):
        pass
```

Then swap the data source in `dsp.py`:

```python
container.register("data_source", lambda: DataSource.CSVReplay("my_recording.csv"))
```

Note that the number of channels must match what the rest of the program expects. The
displays are built for 2 channels; a file with more will only show the first two, and the
sensor-vs-sensor plot assumes exactly 2.

---

## 7. Borrowing one piece for your own script

You don't have to adopt the whole program. The filter classes work perfectly well on their
own, on ordinary saved data, with no hardware and no graphs.

Copy `Filter.py` next to your own script and:

```python
import numpy as np
from Filter import BandPass, Notch

# Your data, shaped (channels, samples).
my_data = np.random.randn(2, 5000)

notch = Notch(sample_freq=1000, notch_freq=50)      # kill 50 Hz mains hum
bp    = BandPass(sample_freq=1000, lowcut=1, highcut=100, order=4)

cleaned = bp.process_chunk(notch.process_chunk(my_data))
print(cleaned.shape)     # (2, 5000) -- same shape in, same shape out
```

Two things to get right:

**Set `sample_freq` to your data's actual sample rate.** It defaults to 1000 Hz. If your data
was recorded at a different rate and you don't say so, the filter will cut the wrong
frequencies — with no error message, just a quietly wrong answer.

**Set `num_channels` if you don't have exactly 2 channels**, e.g.
`BandPass(num_channels=6)`. It defaults to 2 and the internal filter state is sized from it.

If you're processing one complete recording rather than a live stream, you may prefer scipy's
`sosfiltfilt` directly — it runs the filter forwards and backwards to cancel out the phase
delay that `process_chunk` necessarily introduces. That's only possible when you have all the
data up front, which is why this program doesn't do it.

`Filter.py` imports only numpy, scipy and scikit-learn, so borrowing it does **not** drag in
matplotlib or nidaqmx.

---

## 8. Adding a command to the prompt

In `Shell.py`, add a method named `do_yourcommand`. The `cmd` library that `DSPShell`
inherits from finds it automatically — there's no list to update.

```python
def do_hello(self, arg):
    """
    Says hello.
    Usage: hello name
    Example: hello world
    """
    print(f"Hello, {arg}!")
```

- The method name after `do_` is what the user types.
- **Everything typed after the command arrives as one single string** in `arg`, unsplit. If you
  want separate values, use `arg.split()` and convert the types yourself — see `do_bp_filt`.
- **The docstring is the help text.** `help hello` prints it verbatim. Keep the
  Usage/Example format for consistency.
- Reach other objects through `self._container.get_instance("name")`.

**Wrap the body in `try`/`except`.** The shell runs on a daemon thread, and an uncaught
exception used to kill that thread silently — the graphs kept animating but the prompt
stopped responding, with no error shown. That was the cause of former known bugs 1 and 2.
`DSPShell.onecmd` is now overridden to catch anything a `do_*` method throws, so a mistake
here degrades to a printed message instead of a dead prompt. Still catch your own errors: the
backstop gives a generic message, your `except` can give a useful one.

---

## 9. Things that will trip you up

**The shell and the graphs are on different threads.** `plt.show()` blocks the main thread, so
the CLI runs on a separate daemon thread. Anything the CLI touches while data is flowing needs
a lock (`BandPass.change_filt_coeffs` shows the pattern).

**Never touch the figure from the CLI thread.** matplotlib may only be used from the thread
running the GUI event loop — the main thread. Calling `set_title`, `set_ylim` or `draw_idle`
from a `do_*` method is a race against the animation, and matplotlib's own Tk backend warns
that its blit path "is thread unsafe and will crash the process if called from a thread".
`DisplayManager._run_on_gui_thread(op)` exists for this: it queues `op` and `_main_update`
runs it just before the next frame is drawn, i.e. within the 50 ms animation interval.
`change_title_axes`, `set_axis_limits` and `set_auto_scale` all go through it. Follow the same
pattern for anything new that changes the figure from a command.

**`get_instance` raises, it doesn't return `None`.** Code written as
`if container.get_instance("bp") is None:` never works as intended — the call throws
`ValueError` first. Use `try`/`except` (as `do_bp_filt` now does), or check `list_filters()`.

**Displays are laid out by registration order, not by name.** `DisplayManager` fills the grid
left-to-right, top-to-bottom, and hands the raw signal to the first half and the filtered
signal to the second. The titles are labels only. Reorder the `register_display` calls in
`dsp.py` and the data assignment moves with them.

**The grid is always 2 rows.** `cols` is computed as `num_plots // 2`, so register displays in
even numbers or the last one won't be drawn.

**Blitting is off by default.** It's a matplotlib speed optimisation that only redraws the
lines rather than the whole figure. Turning it on (`DisplayManager(blitting=True)`) is much
faster but **freezes the axes**, so auto-scaling stops working and you must set sensible
fixed limits. Worth it only if the animation is too slow.

**PCA needs at least as many channels as components.** Every PCA filter is set to
`n_components=2` and quietly returns the data unmodified if given fewer than 2 channels.

---

## 10. Ideas for future work

Carried over from the original version of this project, still unimplemented:

1. Add and remove **displays** at runtime, the way filters already work.
2. Implement **SSP and SSS** (Signal-Space Projection / Separation). Stubs exist at the bottom
   of `Filter.py`.
3. Allow mixing axes on one plot — e.g. x from sensor 1 against y from sensor 2 — to find
   better-correlated pairs.
4. Run PCA across all 6 channels at once rather than 2 at a time.
5. More diagnostic displays. Plotting scikit-learn's `explained_variance_ratio_` would show
   how much of the signal the first principal component accounts for — i.e. how much is
   common-mode noise.
6. Automatically scan for the sensor configuration with the best correlation, using that same
   `explained_variance_ratio_`.

And, more immediately: **finish the `recording` command.** It is the only one still stubbed
out — `do_recording` looks for `start_recording`/`stop_recording` on `DisplayManager` and
reports that they don't exist. Implementing them (matplotlib's `FFMpegWriter` was the original
intent, see commit `611ae18`) is all that's needed; the shell side already works.
