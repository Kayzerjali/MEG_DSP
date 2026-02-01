import cmd

class DSPShell(cmd.Cmd):
    intro = "Welcome to the MEG DSP Shell. Type help or ? to list commands.\n" # printed to shell
    prompt = "dsp: " # prompt symbol at each line of shell

