# SPDX-License-Identifier: GPL-2.0-only

import argparse
import random
import string
import subprocess
import sys
import time


def main():
    modes = (
        "vorlesen",
        "vorlesen-interaktiv",
        "raten",
        "eingeben",
    )
    char_seqs = {
        "Ziffern": string.digits,
        "Alphabet": string.ascii_uppercase,
        "Vokale": "AEIOU",
        "Ziffern-dann-Alphabet": string.digits + string.ascii_uppercase,
    }
    char_seq_ids = list(char_seqs)
    char_seq_id_default = char_seq_ids[0]

    parser = argparse.ArgumentParser(
        prog="lernstaben",
        formatter_class=argparse.RawTextHelpFormatter,
        description="Lerne Buchstaben auf dem Text-Terminal."
    )
    parser.add_argument(
        "-s", "--character-sequence", dest="char_seq_id",
        default=char_seq_id_default,
        metavar="<identifier>", type=str, choices=char_seq_ids,
        help= "\n".join((
            "Die zu verwendende Zeichenfolge:\n    %s." % (
                "\n    ".join(char_seq_ids),
            ),
            "",
            "Default ist %s." % (char_seq_id_default,),
            "",
            "Siehe auch --character-file .",
        ))
    )
    parser.add_argument(
        "-f", "--character-file", dest="path_char_file",
        metavar="<path>", type=str,
        help= "\n".join((
            "Benutze eine Datei um eine Zeichenfolge daraus zu",
            "generieren.",
            "",
            "Kleinbuchstaben werden zu Großbuchstaben und doppelte",
            "Zeichen werden zusammengefasst. ASCII-Kontrollzeichen",
            "und Leerzeichen werden entfernt. Die entstandene Menge",
            "wird dann sortiert als Zeichenfolge verwendet.",
            "",
            "Wird diese Option verwendet, dann werden zusätzliche",
            "Angaben von --character-sequence ignoriert.",
        ))
    )
    parser.add_argument(
        "mode",
        metavar="<modus>", type=str, choices=modes,
        help="Der zu startende Modus: %s" % (", ".join(modes),)
    )
    args = parser.parse_args()

    char_seq = []
    if args.path_char_file is not None:
        char_seq.extend(gen_char_seq_from_file(args.path_char_file))
    else:
        char_seq.extend(char_seqs[args.char_seq_id])
    with Lernstaben(char_seq) as lernstaben:
        if args.mode == "vorlesen":
            read_characters(lernstaben)
        elif args.mode == "vorlesen-interaktiv":
            interactive_read_characters(lernstaben)
        elif args.mode == "raten":
            interactive_guess_characters(lernstaben)
        elif args.mode == "eingeben":
            interactive_input_characters(lernstaben)


def interactive_read_characters(lernstaben):
    print("Zum Beenden STRG+C drücken.")
    while True:
        s = input("Zeichen --> ")
        lernstaben.select(s.upper())
        lernstaben.play()


def read_characters(lernstaben):
    print("Zum vorzeitigen Beenden STRG+C drücken.")
    while lernstaben.select_next():
        print("  " + lernstaben.get_character()); sys.stdout.flush()
        lernstaben.play()


def interactive_guess_characters(lernstaben):
    msg = (
        "Nach korrekter Eingabe aller Zeichen beendet sich das Programm.\n"
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
            time.sleep(0.6)
            if s == "":
                continue
            elif s.upper() == ch:
                lernstaben.play_feedback(True)
                break
            lernstaben.play_feedback(False)


def interactive_input_characters(lernstaben):
    msg = (
        "Nach korrekter Eingabe aller Zeichen beendet sich das Programm.\n"
        "\n"
        "Nach einer leeren Eingabe, erklingt das vorherige Zeichen erneut.\n"
        "\n"
        "Zum vorzeitigen Beenden STRG+C drücken."
    )
    print(msg)
    ch_prev = None
    while lernstaben.select_next():
        ch = lernstaben.get_character()
        while True:
            s = input("Zeichen --> ")
            time.sleep(0.6)
            if s == "":
                if ch_prev is not None:
                    lernstaben.select(ch_prev.upper())
                    lernstaben.play()
                    lernstaben.select(ch)
                continue
            elif s.upper() == ch:
                ch_prev = ch
                lernstaben.play()
                lernstaben.play_feedback(True)
                break
            lernstaben.play_feedback(False)


def gen_char_seq_from_file(path):
    with open(path) as fh:
        chars = set(fh.read().upper())

    chars_to_remove = [chr(x) for x in range(32)] # control chars
    chars_to_remove.append(chr(32)) # SPACE
    chars_to_remove.append(chr(127)) # control char
    for ch in chars_to_remove:
        if ch in chars:
            chars.remove(ch)

    return sorted(chars)

class Lernstaben:
    def __init__(self, char_seq):
        self.char_player = None
        self.char = None
        self.char_seq_idx = -1
        self.char_seq = char_seq

    def __enter__(self):
        self.char_player = CharacterSoundPlayer("./sounds/")
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

    def play_feedback(self, positive):
        """Play affirmative or try-again audio

        The implementation is quite a stretch as it uses the char_player
        to play words with a length of character name to give the positive
        or negative feedback.
        """
        if positive:
            self.char_player.play("richtig")
        else:
            self.char_player.play("nochmal")


class CharacterSoundPlayer:
    def __init__(self, path_sounds):
        self.validate_path(path_sounds)
        self.mp_slave_cmd_loadfile = "loadfile " + path_sounds + "/%s.mp3"
        self.mp_slave = MPlayerSlave()
        self.mp_slave.start()
        # Compensate possible startup delay. Otherwise we may sleep to short in
        # method play.
        time.sleep(1.5)

    def play(self, char):
        self.mp_slave.send_command(self.mp_slave_cmd_loadfile % (char,))
        time.sleep(1.7)

    def shutdown(self):
        self.mp_slave.send_command("quit")

    def validate_path(selft, path):
        """For now we only allow ASCII letters and dot and slash"""
        allowed_chars = string.digits + string.ascii_letters + "./"
        for ch in path:
            if ch not in allowed_chars:
                raise Exception()


class MPlayerSlave:
    def __init__(self):
        self.mp_process = None

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
