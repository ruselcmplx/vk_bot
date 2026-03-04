from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import List, Tuple


HANGMANPICS = [
    '''
  +------+\n  |\u2005\u2005|\n  |\n  |\n  |\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\n  |\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\u3000\u3000|\n  |\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\u3000\u3000/|\n  |\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\u3000\u3000/|\\\n  |\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\u3000\u3000/|\\\n  |\u3000\u3000/\n  |\n=========''',
    '''
  +------+\n  |\u2005\u2005|\n  |\u3000\u3000O\n  |\u3000\u3000/|\\\n  |\u3000\u3000/ \\n  |\n=========''',
]


@dataclass
class HANGMAN:
    player_id: int
    game_start: int = 0

    def __post_init__(self) -> None:
        self.mistakes: int = 0
        self.win: bool = False
        self.hangman_pic: str = HANGMANPICS[0]
        self.used_letters: List[str] = []
        with open("./mnt/nouns.txt", encoding="utf8") as f:
            word = random.choice(f.readlines()).strip()
        self.word: str = word
        shown_word: List[str] = [word[0]]
        shown_word.extend(["_"] * (len(word) - 2))
        shown_word.append(word[-1])
        self.shown_word: List[str] = shown_word

    def guess(self, letter: str) -> Tuple[bool, str]:
        res_text = ""
        if letter not in self.used_letters:
            self.used_letters.append(letter)

        if letter in self.word[1:-1]:
            shown_word = self.shown_word
            pattern = rf"{letter}"
            matches = re.finditer(pattern, self.word)
            for match in matches:
                i = match.start(0)
                shown_word[i] = self.word[i]
            if "_" not in self.shown_word:
                self.win = True
                res_text = f"Ты победил!\nСлово {self.word}"
            else:
                res_text = " ".join(shown_word)
        else:
            if self.mistakes < 5:
                self.mistakes += 1
                self.hangman_pic = HANGMANPICS[self.mistakes]
                res_text = (
                    f"{self.hangman_pic}\nНет совпадений, использованные буквы: "
                    f"{', '.join(self.used_letters)}\n" + " ".join(self.shown_word)
                )
            else:
                # Финальное состояние — поражение
                self.mistakes += 1
                # Защита от выхода за пределы списка картинок
                idx = min(self.mistakes, len(HANGMANPICS) - 1)
                self.hangman_pic = HANGMANPICS[idx]
                res_text = f"{self.hangman_pic}\nТы проиграл\nСлово {self.word}"
                return False, res_text

        return self.win, res_text


if __name__ == "__main__":
    import time

    game = HANGMAN(player_id=1, game_start=int(time.time()))
    input_phrase = "Слово: " + " ".join(game.shown_word)
    while (not game.win) and game.mistakes < 6:
        guess_letter = input(input_phrase + "\n").strip()
        if guess_letter and len(guess_letter) == 1:
            win, res = game.guess(guess_letter)
            input_phrase = res
        else:
            input_phrase = "Введите букву"

    input("You win\n" if game.win else game.hangman_pic + "\nYou lost\n")
