Spellbound
==========

*Saving the (FOSS) world, one typo at a time.*

Spellbound is a Python script that looks through Github repositories for spelling mistakes (in comments and strings). It has already been successfully applied to find spelling mistakes in repos such as jquery, requests, and reddit.

Installation
------------
First, install the Python spellchecking library enchant.
```
pip install pyenchant
```

Then just clone spellbound.py!

Usage
-----
Running `python spellbound.py [owner] [repository]` will search for spelling errors in that repo.

Running `python spellbound.py [amount]` will search for spelling errors in the [amount] most popular repositories on Github.
