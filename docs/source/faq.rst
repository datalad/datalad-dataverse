.. include:: ./links.inc
.. _intro:

FAQ
===

Q1: Why do my file names look so weird?
---------------------------------------

This is due to restriction that (Dataverse_) currently puts onto file names and directory names.

Let us explain that in a little more detail. Dataverse allows only directory names that have characters from
the english alphabet, numbers, and the characters " ", "-", "_", ".". There are similar restrictions for file names.
That means, Dataverse cannot store a file name like "Änderungen" or "Déchiffrer", due to the "Ä" and "é" in them.
Generally, Dataverse does not support names that contain letters from non-English alphabets.

But we would like to allow you to store all your data reliably in a Dataverse dataset. Therefore we had to advise a
way to "encode" them for Dataverse. In short, every character that is not supported by Dataverse is encoded as
"-<X><X>-", where the "<X>" are hexadecimal digits, i.e. one of "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
"A", "B", "C", "D", "E", "F". Depending on the character there might be two or more such digits. This encoding can be
reverted by a client to yield the original name.

There is one more peculiarity of Dataverse, it "swallows" all " " (space), "-", and "." in the beginning of a directory name.
We compensate for that too, which further "mangles" your directory and file names, if they should start with either
a " ", "-", or ".".

We dislike this name-mangling as much as you probably do. But are forced to use mechanisms to work around the
restrictions of Dataverse, if we want to ensure that all of your data can be stored on and retrieved from a Dataverse
dataset.
