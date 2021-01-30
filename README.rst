ADL
===

Download ebooks from Adobe .acsm files, similar to Adobe Digital Editions (ADE).

There is no Linux version for ADE. To download your DRM-protected purchased books today, you currently need to use ADE on Windows, MacOS X, or Android. Wine is reported to work but I did not have much success.

This program is a command-line tool to perform the same task.

What it does
------------
- Allow you to login with your Adobe ID. You can log in as anonymous with some restrictions (see below)
- Download your epub from the acsm file. However, if your file is protected by DRM, you will obtain an encrypted epub.

What it does not yet do
-----------------------
- Allow you to transfer the book on your device for reading

What it will not do
-------------------
- Remove the DRM from your book

You may wonder how useful it is to be able to download an encrypted book! Well, hopefully in the (near ?) future, I will figure out the last piece, which is to transfer it onto your reader in such a way that it can actually read it. Or if you know how to do that already, don't hesitate, I will welcome any contributor :-)

How to use
==========

Login
-----
Use::

  ./adl login 

You only need to login once, to exchange encryption keys.

I recommend you to create an ID on Adobe website. It is possible to login as Anonymous but be aware that you may lose access to your books: if you lose your private key (stored locally), by mistake or in case of program error. With an Adobe ID, the keys are stored on Adobe side and can be retrieved from any place.
As far as I understand, it is also possible to use other IDs to log in, but this is not supported yet

You can login several times if you have several accounts.

Download
--------

Download a file with::

  ./adl get -f <file.acsm>

Manage accounts
---------------

In case you have logged in several times, list your current accounts with::

  ./adl account list

And change the currently used account with::

  ./adl.py account use <account urn>


