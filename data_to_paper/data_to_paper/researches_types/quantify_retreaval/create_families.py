import random
import numpy as np

from typing import NamedTuple

FERTILITY = 3
N_GENERATIONS = 3
N_FAMILIES = 200

# 1 + 3 + 3^2 + 3^3 + ... + 3^n = (3^(n+1) - 1) / 2
family_size = (FERTILITY ** N_GENERATIONS - 1) // 2
number_of_persons = family_size * N_FAMILIES


class Person(NamedTuple):
    last_name: str
    gender: str  # F/M


# read the last_names.txt file
names = []
with open('data/last_names.txt', 'r') as f:
    for line in f:
        # get the last name, if there are multiple words, take the first one
        line = line.strip()
        if line:
            first_word = (line + ' ').split()[0]
            if len(first_word) > 2 and first_word.isalpha():
                names.append(first_word)


names = sorted(list(set(names)))

# create a list of Persons, assign random gender to each person
persons = []
for name in names:
    persons.append(Person(name, random.choice(['F', 'M'])))


# choose number_of_persons persons randomly
persons = random.sample(persons, number_of_persons)


# persons is organized family by family, generation by generation
# each family has 1 parent, 3 children, 9 grandchildren, 27 great-grandchildren, etc.

families = []
for i in range(N_FAMILIES):
    family = persons[i * family_size: (i + 1) * family_size]
    families.append(family)

# create pairs of parent-child
# a family is organized as follows:
#           0
#   1       2       3
# 4 5 6   7 8 9  10 11 12

# create a list of parent-child pairs of indices for a single family
# [(0, 1), (0, 2), (0, 3), (1, 4), (1, 5), (1, 6), (2, 7), (2, 8), (2, 9), (3, 10), (3, 11), (3, 12)]
parent_child_indices = []
for i in range(N_GENERATIONS - 1):
    for parent in range((FERTILITY ** i - 1) // 2, (FERTILITY ** (i + 1) - 1) // 2):
        for child in range(FERTILITY * parent + 1, FERTILITY * parent + FERTILITY + 1):
            parent_child_indices.append((parent, child))


# create a list of parent-child pairs of persons for all families
parent_child_pairs = []
for family in families:
    for parent, child in parent_child_indices:
        parent_child_pairs.append((family[parent], family[child]))


# create a sentence for each pair
sentences = []
for parent, child in parent_child_pairs:
    son_or_daughter = 'son' if child.gender == 'M' else 'daughter'
    sentence = f'{child.last_name} is the {son_or_daughter} of {parent.last_name}.'
    sentences.append(sentence)

# join all sentences in random order
story = '\n'.join(random.sample(sentences, len(sentences)))

print(story)
print()
for person in families[0]:
    print(person)
