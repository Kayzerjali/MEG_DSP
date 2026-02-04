## How to use
Navigate to folder in a CLI. Run "python dsp.py". Graphs will appear and real time configuration is available through the terminal. 
There are no filters applied initally. Use add_filter 'filter name' to add filters, use list_filters to list available filters


## Dependancies
1) scikit-learn : "pip install scikit-learn"
2) FFmpeg: navigate to ffmpeg website. Click download but dont download source code. Hover over windows icon to and download the zip from 'Windows builds by BtbN'. Extract the zip to C: drive. Add the path to the bin folder inside the extracted ffmpeg file by going to 'environment varibales' in windows search. Double click 'path', click new and add the file path to bin folder. Test by running ffmeg in cmd. If didnt work try adding the ffmpeg path to other path varibale (there is user and system). 
After this run 'pip install ffmpeg-python'

## Notes 
autoscale for Filtered freq domain not working such that cannot see top
Be able to easily add notch filters and switch and remove filters 
raw time domain graph sometimes I cant find the signal (looks like no signal on graph)
be able to start recording to save animation, and stop
On y axis I turned on signal but couldnt see it in the filtered but saw it in raw

remove filter not working
set_axis_limits still not working