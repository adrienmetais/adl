ADL
===

Download ebooks from Adobe .acsm files, similar to Adobe Digital Editions (ADE).

There is no Linux version of ADE. To download your DRM-protected purchased books today, you currently need to use ADE on Windows, MacOS X, or Android. Wine is reported to work but I did not have much success.

This program is a command-line tool to perform the same task. It was tested only on Linux.

What it does
------------
- Allow you to login with your Adobe ID. You can log in as anonymous with some restrictions (see below)
- Download your epub from the acsm file. However, if your file is protected by DRM, you will obtain an encrypted epub.
- Activate a new ebook reader that supports ADEPT (Adobe) DRM

You may wonder how useful it is to be able to download an encrypted book ! Well, hopefully in the (near ?) future, I will finish the last piece, which is to transfer it onto your reader in such a way that it can actually read it. 

What it does not yet do
-----------------------
- Allow you to transfer the book on your device for reading

What it will not do
-------------------
- Remove the DRM from your book

Disclaimer
----------
This tool is suited above all to my purpose. It has not been tested extensively, nor in any other setup. Use at your own risks.

How to use
==========

For the moment, you need to call the adl.py script from the same repository. I'll work on that when I have some time.

Login
-----
Use::

  ./adl.py login <-u adobeID>

You only need to login once, to exchange encryption keys.

I recommend to login with an Adobe ID (which can be created on Adobe website). It is possible to login as Anonymous, but be aware that you may lose access to your book if something goes wrong during download. Also, you will not be able to download it again if you ever lose the private key (or if you use another client). With an Adobe ID, the keys and the books are attached to your account: you can login from somewhere else and get them back.
As far as I understand, it is also possible to use other IDs to log in, but this is not supported yet.

You can login several times if you have several accounts.

Download
--------

Download a file with::

  ./adl.py get -f <file.acsm>

Manage accounts
---------------

In case you have logged in several times, list your current accounts with::

  ./adl.py account list

And change the currently used account with::

  ./adl.py account use <account urn>

Activate a device
-----------------

Mount the root of your device somewhere, and select the account you want to use. Then::

  ./adl.py device register <mountpoint>

Several cases may occur:
- The device has never been activated with ADE (or adl): activate the device
- The device has already been activated for your user: nothing will be done on your device, but adl's db will be updated
- The device has already been activated for an unknown user: nothing will be done, to avoid losing access to books on the device
