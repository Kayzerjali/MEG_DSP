# MEG_DSP — Live signal viewer for MEG sensors

This program reads the signal coming out of two magnetic field sensors, cleans it up
with filters, and draws live graphs of it on your screen while it happens. You can turn
filters on and off by typing commands, and the graphs change immediately.

**You do not need any sensors or special hardware to try this.** If the program can't find
the real hardware, it automatically switches to a built-in fake signal generator so you can
still see everything working. That makes it a safe way to learn what the program does before
you plug anything in.

---

## Table of contents

1. [Getting the program onto your computer](#1-getting-the-program-onto-your-computer)
2. [Installing Python](#2-installing-python)
3. [Opening a terminal in the right folder](#3-opening-a-terminal-in-the-right-folder)
4. [Installing the libraries the program needs](#4-installing-the-libraries-the-program-needs)
5. [Running the program](#5-running-the-program)
6. [What you're looking at](#6-what-youre-looking-at)
7. [Your first five minutes — a guided tour](#7-your-first-five-minutes--a-guided-tour)
8. [All the commands](#8-all-the-commands)
9. [Using the real sensors](#9-using-the-real-sensors)
10. [When something goes wrong](#10-when-something-goes-wrong)
11. [Known bugs](#11-known-bugs)
12. [Glossary](#12-glossary)
13. [Extending or reusing the code](#13-extending-or-reusing-the-code)
14. [Contact](#14-contact)

---

## 1. Getting the program onto your computer

Pick **one** of these two options. Option A is simpler; use it if the words "git" or
"repository" mean nothing to you.

### Option A — Just download the files (easiest)

1. Go to the project's page on GitHub in your web browser.
2. Click the green **`< > Code`** button near the top right.
3. Click **Download ZIP**.
4. Find the downloaded `.zip` file (usually in your `Downloads` folder).
5. **Right-click it → "Extract All..." → "Extract".** This step matters — Windows will happily
   let you look *inside* a zip file without extracting it, but the program will not run from in
   there. You need a real, normal folder.
6. You should now have a folder called something like `MEG_DSP` containing `dsp.py`,
   `Filter.py`, `Display.py` and a few others. Remember where it is.

### Option B — Use git

Git is a tool that downloads the code *and* lets you pull down future updates with one
command. If you don't have it, get it from [git-scm.com](https://git-scm.com/downloads) and
accept every default option in the installer.

Then open PowerShell and run:

```powershell
cd $HOME\Documents
git clone <the-url-of-this-repository>
cd MEG_DSP
```

`cd` means "change directory", i.e. "go into this folder". Later, to fetch any updates the
author has made, run `git pull` from inside the folder.

You do not need to understand git to use this program. Option A is completely fine.

---

## 2. Installing Python

Python is the language this program is written in. Your computer probably doesn't have it yet.

1. Go to [python.org/downloads](https://www.python.org/downloads/).
2. Click the big yellow **Download Python** button.
3. Run the installer. **Before clicking Install, tick the checkbox at the bottom that says
   "Add python.exe to PATH".** This is the single most commonly missed step, and skipping it
   causes the `python is not recognized` error later. If you miss it, just run the installer
   again and tick it.
4. Click Install Now and wait.

To check it worked, open PowerShell (press the Windows key, type `powershell`, press Enter)
and run:

```powershell
python --version
```

You should see something like `Python 3.13.1`. Any version 3.10 or newer is fine. This
program has been tested on Python 3.13 and 3.14.

If you instead see an error, restart your computer and try once more — the PATH setting
sometimes only takes effect after a restart.

---

## 3. Opening a terminal in the right folder

This is the step that trips up nearly everyone, so here's the reliable trick.

1. Open **File Explorer** and navigate into the `MEG_DSP` folder — the one where you can see
   `dsp.py` with your own eyes.
2. Click once on the **address bar** at the top (the strip showing the folder path). The text
   will highlight.
3. Type `powershell` over the top of it and press **Enter**.

A blue terminal window opens, already sitting in the correct folder. To prove it, run:

```powershell
ls
```

`ls` means "list" and shows the files in the current folder. You should see `dsp.py`,
`Filter.py`, `Display.py`, `DataSource.py`, `Container.py`, `Shell.py`. If you see those, you
are in the right place and can continue.

If you see something else, you're in the wrong folder — go back to step 1.

> **On a Mac:** right-click the folder and choose *New Terminal at Folder*. If you don't see
> that option, enable it in System Settings → Keyboard → Keyboard Shortcuts → Services.

---

## 4. Installing the libraries the program needs

The program needs five libraries: **numpy** and **scipy** (maths), **matplotlib** (graphs),
**scikit-learn** (the PCA filters), and **nidaqmx** (talking to the sensor hardware).

`nidaqmx` is required **even if you have no hardware** — the program imports it at startup
regardless. It installs fine on any computer, so just install all five.

### Recommended: use a virtual environment

A virtual environment is a private box of libraries that belongs to this project only. It stops
this project's libraries from clashing with any other Python thing on your computer. It costs
you two extra commands and saves a lot of pain.

In your terminal from section 3, run these **one at a time**:

```powershell
python -m venv venv
```

```powershell
.\venv\Scripts\Activate.ps1
```

```powershell
pip install -r requirements.txt
```

That last one prints a lot of scrolling text for a minute or two. That's normal. You'll know
it finished when it prints `Successfully installed ...` and gives you back a prompt you can
type at.

After activating, your prompt gets a `(venv)` prefix, like this:

```
(venv) PS C:\Users\you\Documents\MEG_DSP>
```

**That `(venv)` prefix is important.** It means the private box is switched on. Every time you
open a new terminal to use this program, you must run the `Activate.ps1` line again — but
`python -m venv` and `pip install` are one-time-only.

> **If PowerShell refuses to activate** with a message about "running scripts is disabled on
> this system", run this once and then retry the activate line:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
>
> This is a standard, safe Windows setting that permits locally-created scripts to run.

### Simpler alternative

If the virtual environment is causing you grief, skip it. This installs the libraries for your
whole computer instead, which is slightly messier but works fine:

```powershell
pip install -r requirements.txt
```

---

## 5. Running the program

One command:

```powershell
python dsp.py
```

Two things happen:

**A window opens** with six live, moving graphs.

**Your terminal turns into a control panel.** It prints a welcome message and the prompt
changes to `dsp:` — that's where you type commands to change what the graphs do:

```
Welcome to the MEG DSP Shell. Type help or ? to list commands.

dsp:
```

If you have no sensor hardware attached, you'll first see this, which is completely
expected and not an error:

```
Warning: Could not initialize NIDAQ (...).
Switching to MockSignal for simulation.
```

That means it's running on the built-in fake signal. Everything works normally.

**To stop the program:** type `quit` and press Enter, or just close the graph window. If it
gets stuck, click on the terminal and press **Ctrl+C**.

---

## 6. What you're looking at

Six graphs in two rows of three. **The top row is always the raw, untouched signal. The
bottom row is the same signal after your filters have been applied.** That side-by-side
layout is the whole point of the program — it shows you what your filtering is actually doing.

When you first start up there are **no filters applied**, so the top and bottom rows are
identical. That's correct, not a bug. They diverge as soon as you add a filter.

|  | Left column | Middle column | Right column |
|---|---|---|---|
| **Top row** | Raw time domain | Raw frequency domain | Raw sensor-vs-sensor |
| **Bottom row** | Filtered time domain | Filtered frequency domain | Filtered sensor-vs-sensor |

**Time domain** — the classic wiggly line. Signal strength (in picotesla) going up and down
as time passes. Shows the most recent 1 second.

**Frequency domain** — the same signal broken down into "how much of each frequency is in
here". A tall spike at 50 Hz means a strong 50 Hz hum, which is almost always electrical
interference from mains power. This is where you *see* a filter working: switch on the notch
filter and watch that spike collapse in the bottom row.

**Sensor-vs-sensor (labelled PCA)** — a scatter plot with sensor 1 on the horizontal axis and
sensor 2 on the vertical axis. If the two sensors are picking up the same background noise,
the dots form a tight diagonal line. Ambient noise hits both sensors equally, but a real brain
signal wouldn't — so this plot is a quick visual check of how much of what you're seeing is
just shared noise.

Both sensors are drawn on each graph, labelled `Ch 1` and `Ch 2`.

---

## 7. Your first five minutes — a guided tour

Start the program, then type these at the `dsp:` prompt one at a time and watch the graph
window after each. This is the fastest way to understand what the program is for.

**Step 1.** See which filters are available:

```
list_registered_filters
```

**Step 2.** Add the notch filter, which removes 50 Hz mains hum:

```
add_filt notch
```

Now look at the middle column. The top graph still has its spike at 50 Hz; the bottom graph's
spike has been cut away. That's the filter working. You just cleaned a signal.

**Step 3.** Add a bandpass filter, which throws away everything except a chosen frequency
band:

```
add_filt bp
```

The bottom row changes a lot. By default it keeps only 5–40 Hz.

**Step 4.** Change the band to keep 1–100 Hz instead, with a filter steepness of 4:

```
bp_filt 1 100 4
```

**Step 5.** Check what you've got switched on:

```
list_current_filters
```

**Step 6.** Clear everything and watch the two rows become identical again:

```
remove_filt all
```

**Step 7.** Try the noise-removal filter and watch the right-hand scatter plot:

```
add_filt pca
```

The top-right plot keeps its tight diagonal line. The bottom-right one scatters into a blob,
because `pca` finds whatever the two sensors have in common and subtracts it out. The
diagonal *was* the shared noise, and now it's gone.

**Step 8.** Finish up:

```
quit
```

You now know how to drive the whole program.

---

## 8. All the commands

Type these at the `dsp:` prompt. Typing `help` lists them, and `help add_filt` explains any
single one.

### Filters

| Command | What it does |
|---|---|
| `list_registered_filters` | Show every filter you're allowed to add. |
| `list_current_filters` | Show which filters are switched on right now. |
| `add_filt NAME` | Switch a filter on. Example: `add_filt notch` |
| `remove_filt NAME` | Switch a filter off. Example: `remove_filt notch` |
| `remove_filt all` | Switch off every filter at once. |
| `bp_filt LOW HIGH ORDER` | Retune the bandpass filter. Example: `bp_filt 50 250 5` |

Filters stack in the order you add them. Adding `notch` then `bp` runs the signal through
the notch filter first, then the bandpass filter.

### The filter names you can use

| Name | What it does |
|---|---|
| `bp` | **Bandpass.** Keeps a chosen frequency range and discards the rest. Defaults to 5–40 Hz. Retune it with `bp_filt`. |
| `notch` | **Notch.** Surgically removes one narrow frequency — set to 50 Hz for Australian mains hum. Use this one first; mains interference is usually the biggest thing in the signal. |
| `pca` | **Principal Component Analysis.** Finds the strongest pattern the two sensors share and subtracts it. Since both sensors sit in the same room, that shared pattern is mostly ambient noise. |
| `ipca` | **Incremental PCA.** Same idea, but it keeps learning and adapting as new data arrives instead of judging each chunk on its own. Better if the noise drifts over time. |
| `spca` | **Sparse PCA.** A variant of `pca`. Slower. |
| `kpca` | **Kernel PCA.** Can catch non-linear patterns that plain `pca` misses. ⚠️ **Very heavy — it can freeze a weaker laptop.** Save your work before trying it. |

If you're not sure what to use, start with `notch`, then add `bp`.

### Display

| Command | What it does |
|---|---|
| `axis x` / `axis y` / `axis z` | Switch which direction of magnetic field the sensors report. |
| `axis mag` | Combine all three directions into a single overall strength. |
| `set_axis_limits (ROW,COL) MIN MAX` | Pin one graph's vertical scale so it stops auto-rescaling. Example: `set_axis_limits (1,0) -2000 2000` |
| `set_auto_scale (ROW,COL)` | Undo the above and let the graph rescale itself again. |

For `ROW` and `COL`, counting starts at **zero**: the top row is `0`, the bottom row is `1`;
columns are `0`, `1`, `2` from left to right. So the bottom-middle graph is `(1,1)`.
Note there is no space after the comma.

Pinning the scale is useful because a single large spike can auto-rescale a graph so hard
that everything else looks like a flat line.

### Other

| Command | What it does |
|---|---|
| `help` | List every command. |
| `help COMMAND` | Explain one command. |
| `quit` | Close the program. |

---

## 9. Using the real sensors

Skip this section entirely if you're just exploring with the simulated signal.

The program reads from a **National Instruments DAQ** device, which is the box that converts
the sensors' analog output into numbers the computer can read.

**You need the NI-DAQmx driver.** The `nidaqmx` library you installed with pip is only a
translator — the actual driver is separate software from National Instruments, and without it
the program will always fall back to the simulated signal. Download it from the NI website
and install it, then restart the program.

**Expected wiring.** The code assumes the device is named `Dev1` and the sensors are wired
to these channels:

| `axis` setting | Channels read |
|---|---|
| `x` | `Dev1/ai0`, `Dev1/ai3` |
| `y` | `Dev1/ai1`, `Dev1/ai4` |
| `z` | `Dev1/ai2`, `Dev1/ai5` |
| `mag` | all six at once, combined into one strength per sensor |

So sensor 1 is on `ai0`–`ai2` and sensor 2 is on `ai3`–`ai5`, x/y/z in order.

If your device has a different name or wiring, edit the `set_axis` method in `DataSource.py`.
You can check the real name in NI MAX, the utility that ships with the driver.

**Settings you may need to change**, all near the top of `DataSource.py` in the `NIDAQ` class:

- **Sample rate** — 1000 readings per second by default.
- **Voltage-to-field conversion** — the code assumes **2.7 V/nT** and reports picotesla.
  If your sensors have a different sensitivity, this number is wrong and every reading will be
  scaled incorrectly. It's in `get_data`.

**Confirming it's using real data:** if you don't see the `Switching to MockSignal` warning at
startup, you're on real hardware.

---

## 10. When something goes wrong

Find your error message below. The exact wording may differ slightly.

**`python : The term 'python' is not recognized...`**
Python isn't installed, or the "Add python.exe to PATH" box wasn't ticked. Redo section 2 and
make sure you tick it. Restart your computer afterwards. If it still fails, try `py dsp.py`
instead — Windows sometimes installs it under the name `py`.

**`can't open file '...dsp.py': [Errno 2] No such file or directory`**
Your terminal is in the wrong folder. Redo section 3, and check that `ls` shows `dsp.py`.

**`ModuleNotFoundError: No module named 'numpy'`** (or `scipy`, `sklearn`, `matplotlib`,
`nidaqmx`)
The libraries aren't installed, or your virtual environment isn't switched on. Check that
your prompt starts with `(venv)`. If it doesn't, run `.\venv\Scripts\Activate.ps1` again. If
it does, run `pip install -r requirements.txt` again.

**`Activate.ps1 cannot be loaded because running scripts is disabled on this system`**
Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, then try again.

**`Warning: Could not initialize NIDAQ ... Switching to MockSignal`**
Not an error. No sensor hardware was found, so you're on the simulated signal. See
section 9 if you were expecting real hardware.

**The graph window opened but everything is a flat line**
Most likely one graph auto-scaled to a huge spike. Use `set_axis_limits` to pin a sensible
range, e.g. `set_axis_limits (1,0) -2000 2000`. Also check you haven't applied a filter that
removes everything — try `remove_filt all`.

**The graphs are frozen / the window says "Not Responding"**
Almost certainly `kpca`, which is too slow for most machines. Press **Ctrl+C** in the
terminal to kill it, restart, and don't use `kpca`.

**No graph window appeared at all**
It may have opened behind your other windows — check the taskbar. Otherwise look for a red
error message in the terminal.

**I typed a command and nothing happened, and now nothing works**
This used to be caused by two commands that killed the prompt (see section 11); both are
fixed. A failing command now prints `Command failed: ...` and keeps the prompt alive. If the
prompt really is unresponsive, close the window and restart the program.

**`Error adding filter: Provider banana not registered`**
That filter name doesn't exist. Run `list_registered_filters` to see the valid ones. They're
short: `bp`, `notch`, `pca`, `ipca`, `spca`, `kpca`.

---

## 11. Known bugs

The three bugs previously listed here have been fixed. What changed:

**1. `recording` no longer breaks the prompt.**
The save-to-video feature was never finished, so the command now says so and does nothing.
It used to kill the `dsp:` prompt. To capture a graph, use the save icon in the graph
window's toolbar.

**2. `bp_filt` no longer breaks the prompt if the bandpass filter isn't loaded.**
It now prints "Bandpass filter not initialized. Use 'add_filt bp' to add it first." as it
always should have.

**3. `set_auto_scale` now works on the right-hand column.**
Column `2` was rejected as out of range. All six graphs accept it.

Also fixed, though it was never written down: **switching `axis` while the graphs were live
could occasionally crash or error.** The `dsp:` prompt and the graphs run on two different
threads, and the prompt was redrawing the graph window directly from its own thread, which is
not allowed. Display changes are now handed to the graph thread and applied on its next
frame — within about 50 ms, so it still looks instant.

**One remaining known weak spot (real hardware only).** If switching `axis` fails to
reconfigure the DAQ — for example the device hasn't released the channels yet — the program
can stop with an error a moment later, when it next tries to read. This has not been
reproduced without hardware, so it is not fixed. If it happens, restart the program and
switch axes less rapidly.

Any command that does fail now prints the error and leaves the prompt running, rather than
silently killing it.

---

## 12. Glossary

**Channel** — one stream of numbers from one sensor. This program uses two, `Ch 1` and `Ch 2`.

**CLI / shell / terminal / command prompt** — all roughly mean "the window where you type
commands". The `dsp:` prompt is this program's own mini-CLI.

**Filter** — anything that takes the signal in and gives a modified signal out, usually to
remove something unwanted.

**Frequency domain** — describing a signal by which frequencies it contains rather than by
its shape over time. Produced by a maths operation called an FFT.

**MEG (magnetoencephalography)** — measuring the tiny magnetic fields produced by electrical
activity in the brain.

**Notch filter** — removes one narrow frequency, typically mains hum at 50 or 60 Hz.

**pT (picotesla)** — the unit of magnetic field strength here. A millionth of a millionth of a
tesla. Brain signals are around this size, which is why ambient noise is such a problem.

**PCA (Principal Component Analysis)** — a technique that finds the dominant shared pattern
across several channels. Here, that shared pattern is assumed to be noise hitting both
sensors equally, so removing it leaves behind what's unique to each sensor.

**Sample rate** — how many readings are taken per second. 1000 Hz here.

**Time domain** — describing a signal by its value over time. The normal wiggly line.

**Virtual environment (venv)** — a private, per-project box of libraries.

---

## 13. Extending or reusing the code

If you want to modify the program, add your own filter, or lift a piece of it into your own
project, see **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** — it explains what each file does, how
data flows through the program, and how to add things.

---

## 14. Contact

s49621169@student.uq.edu.au
