# Lernstaben

*Lernstaben* is a small software package for learning how to pronounce the
characters one can type on a given computer device.

It is intended to be usable on a computer without network access and without
a graphical user interface or a web browser.

The current focus is on German digits and letters. The development is done
in a way to get results as quick as possible. The software is usable, but
still in a very early stage of its development.


## License

This software is licensed under GPL v2 only. See LICENSE.txt file.


## Dependencies

A working *mplayer*[1] executable is needed at run-time. It is used to play
the sounds while the program is running.

You will need to provide MP3 audio files with a voice saying the individual
characters; one per file. There is a program *gen-sounds* that can be used
at build time to generate those files with the help of the Google Translate
TTS engine.


## Usage

On a text terminal start the *lernstaben* program as follows:

    ./lernstaben -h

It should print out a help text on the terminal and you should be able to
work things out from there.


## References

1: MPlayer project: https://mplayerhq.hu
