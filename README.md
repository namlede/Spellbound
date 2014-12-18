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
```
python spellbound.py [owner] [repository]`
```

searches for spelling errors in the specified repo.

```
python spellbound.py [owner] [repository]
```

searches for spelling errors in all the repositories owned by the specified user.

```
python spellbound.py [amount]
```

searches for spelling errors in the [amount] most popular repositories on Github.
