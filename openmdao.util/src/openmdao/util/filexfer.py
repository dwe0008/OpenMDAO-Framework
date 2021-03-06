import fnmatch
import glob
import os
import sys
import zipfile

from openmdao.util.log import NullLogger


def filexfer(src_server, src_path, dst_server, dst_path, mode=''):
    """
    Transfer a file from one place to another.

    If `src_server` or `dst_server` is None, then the :mod:`os` module
    is used for the source or destination respectively.  Otherwise the
    respective object must support :meth:`open`, :meth:`stat`, and
    :meth:`chmod`.

    After the copy has completed, permission bits from :meth:`stat` are set
    via :meth:`chmod`.

    src_server: Proxy
        Host to get file from.

    src_path: string
        Path to file on `src_server`.

    dst_server: Proxy
        Host to put file to.

    dst_path: string
        Path to file on `dst_server`.

    mode: string
        Mode settings for :func:`open`, not including 'r' or 'w'.
    """
    if src_server is None:
        src_file = open(src_path, 'r'+mode)
    else:
        src_file = src_server.open(src_path, 'r'+mode)

    try:
        if dst_server is None:
            dst_file = open(dst_path, 'w'+mode)
        else:
            dst_file = dst_server.open(dst_path, 'w'+mode)

        if src_server is None and dst_server is None:
            chunk = 1 << 20  # 1MB locally.
        else:
            chunk = 1 << 17  # 128KB over network.

        try:
            data = src_file.read(chunk)
            while data:
                dst_file.write(data)
                data = src_file.read(chunk)
        finally:
            dst_file.close()
    finally:
        src_file.close()

    if src_server is None:
        mode = os.stat(src_path).st_mode
    else:
        mode = src_server.stat(src_path).st_mode
    if dst_server is None:
        os.chmod(dst_path, mode)
    else:
        dst_server.chmod(dst_path, mode)


def pack_zipfile(patterns, filename, logger=NullLogger):
    """
    Create 'zip' file `filename` of files in `patterns`.
    Returns ``(nfiles, nbytes)``.

    patterns: list
        List of :mod:`fnmatch` style patterns.

    filename: string
        Name of zip file to create.

    logger: Logger
        Used for recording progress.
    """
    nfiles = 0
    nbytes = 0
    zipped = zipfile.ZipFile(filename, 'w')
    try:
        for pattern in patterns:
            for path in glob.glob(pattern):
                size = os.path.getsize(path)
                logger.debug("packing '%s' (%d)...", path, size)
                zipped.write(path)
                nfiles += 1
                nbytes += size
    finally:
        zipped.close()
    return (nfiles, nbytes)


def unpack_zipfile(filename, logger=NullLogger, textfiles=None):
    """
    Unpack 'zip' file `filename`.
    Returns ``(nfiles, nbytes)``.

    filename: string
        Name of zip file to unpack.

    logger: Logger
        Used for recording progress.

    textfiles: list
        List of :mod:`fnmatch` style patterns specifying which upnapcked files
        are text files possibly needing newline translation. If not supplied,
        the first 4KB of each is scanned for a zero byte. If not found then the
        file is assumed to be a text file.
    """
    # ZipInfo.create_system code for local system.
    local_system = 0 if sys.platform == 'win32' else 3

    nfiles = 0
    nbytes = 0
    zipped = zipfile.ZipFile(filename, 'r')
    try:
        for info in zipped.infolist():
            filename = info.filename
            size = info.file_size
            logger.debug('unpacking %r (%d)...', filename, size)
            zipped.extract(info)
            if info.create_system != local_system:
                if textfiles is None:
                    with open(filename, 'rb') as inp:
                        data = inp.read(1 << 12)
                    if '\0' not in data:
                        logger.debug('translating %r...', filename)
                        translate_newlines(filename)
                else:
                    for pattern in textfiles:
                        if fnmatch.fnmatch(filename, pattern):
                            logger.debug('translating %r...', filename)
                            translate_newlines(filename)
            nfiles += 1
            nbytes += size
    finally:
        zipped.close()
    return (nfiles, nbytes)


def translate_newlines(filename):
    """
    Translate the newlines of `filename` to the local standard.

    filename: string
        Name of the file to be translated.
        The translated file will replace this file.
    """
    with open(filename, 'rU') as inp:
        with open('__translated__', 'w') as out:
            for line in inp:
                out.write(line)
    os.remove(filename)
    os.rename('__translated__', filename)

