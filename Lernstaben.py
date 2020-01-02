# SPDX-License-Identifier: GPL-2.0-only

import argparse
import random
import subprocess
import sys
import time


def main():
    modes = (
        "vorlesen",
        "vorlesen-interaktiv",
        "raten",
    )

    parser = argparse.ArgumentParser(
        prog="lernstaben",
        description="Lerne Buchstaben auf dem Text-Terminal."
    )
    parser.add_argument(
        "mode",
        metavar="<modus>", type=str, choices=modes,
        help="Der zu startende Modus: %s" % (", ".join(modes),)
    )
    args = parser.parse_args()

    with Lernstaben() as lernstaben:
        if args.mode == "vorlesen":
            read_characters(lernstaben)
        elif args.mode == "vorlesen-interaktiv":
            interactive_read_characters(lernstaben)
        elif args.mode == "raten":
            interactive_guess_characters(lernstaben)


def interactive_read_characters(lernstaben):
    print("Zum Beenden STRG+C drücken.")
    while True:
        s = input("Zeichen --> ")
        lernstaben.select(s.upper())
        lernstaben.play()


def read_characters(lernstaben):
    print("Zum vorzeitigen Beenden STRG+C drücken.")
    while lernstaben.select_next():
        lernstaben.play()


def interactive_guess_characters(lernstaben):
    msg = (
        "Nach korrekter Eingabe aller Zeichern beendet sich das Programm.\n"
        "\n"
        "Nach einer leeren oder falschen Eingabe, erklingt das gesuchte\n"
        "Zeichen erneut.\n"
        "\n"
        "Zum vorzeitigen Beenden STRG+C drücken."
    )
    print(msg)
    lernstaben.shuffle_characters()
    while lernstaben.select_next():
        ch = lernstaben.get_character()
        while True:
            lernstaben.play()
            s = input("Zeichen --> ")
            if s == "":
                continue
            elif s.upper() == ch:
                break


class Lernstaben:
    char_player = None
    char = None
    char_seq_idx = -1
    char_seq_digits = [ "0", "1", "2", "3", "4", "5", "6", "7", "8", "9" ]
    char_seq_alphabet = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
        "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X",
        "Y", "Z"
    ]
    char_seq = []
    char_seq.extend(char_seq_digits)
    char_seq.extend(char_seq_alphabet)

    def __enter__(self):
        self.char_player = CharacterSoundPlayer()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.char_player.shutdown()

    def shuffle_characters(self):
        random.shuffle(self.char_seq)

    def get_character(self):
        return self.char

    def select(self, char):
        self.char = char

    def select_next(self):
        if self.char is None:
            self.char_seq_idx = -1

        char_seq_idx_new = min(self.char_seq_idx + 1, len(self.char_seq) - 1)
        has_advanced = char_seq_idx_new > self.char_seq_idx
        self.char_seq_idx = char_seq_idx_new

        self.char = self.char_seq[self.char_seq_idx]

        return has_advanced

    def play(self):
        self.char_player.play(self.char)


class CharacterSoundPlayer:
    mp_slave = None

    def __init__(self):
        self.mp_slave = MPlayerSlave()
        self.mp_slave.start()
        # Compensate possible startup delay. Otherwise we may sleep to short in
        # method play.
        time.sleep(1.5)

    def play(self, char):
        self.mp_slave.send_command("loadfile sounds/" + char + ".mp3")
        time.sleep(1.5)

    def shutdown(self):
        self.mp_slave.send_command("quit")


class MPlayerSlave:
    mp_process = None

    def __init__(self):
        pass

    def start(self):
        if self.mp_process != None:
            return
        cmd = ["mplayer", "-really-quiet", "-slave", "-idle"]
        #print("Starting MPlayer process: " + repr(cmd))
        proc = subprocess.Popen(
            cmd,
            stdin  = subprocess.PIPE,
            stderr = subprocess.PIPE,
            close_fds = True, # will not work as expected on Windows (standard streams redirection)
            shell = False
        )
        self.mp_process = proc


    def send_command(self, command):
        cmd = command + "\n"
        #print(cmd)
        cmd = cmd.encode("UTF-8")
        try:
            self.mp_process.stdin.write(cmd)
        except IOError:
            self.mp_process = None
            self.start()
            self.mp_process.stdin.write(cmd)
        self.mp_process.stdin.flush()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
