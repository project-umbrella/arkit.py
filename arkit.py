'''
ARK: Survival Evolved Toolkit

Only supports Python3, Python2 is end of life and outdated thus not supported.

Purpose:
  Provide a Python toolkit for ARK. Originally designed to unpack the workshop archives.
'''


import struct
import zlib
import sys
import logging


__author__ = "James E"
__contact__ = "https://github.com/james-d-elliott/arkit.py"
__copyright__ = "Copyright 2015, Project Umbrella"
__version__ = "0.0.0.1"
__status__ = "Prototype"
__date__ = "16 October 2015"
__license__ = "GPL v3.0 https://github.com/project-umbrella/arkit.py/blob/master/LICENSE"


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def unpack(src, dst):
    '''
    Unpacks ARK's Steam Workshop *.z archives.

    Accepts two arguments:
        src = Source File/Archive
        dst = Destination File

    Error Handling:
        Currently only logs errors with an archive integrity. Also logs some debug and info messages.
        All file system errors are handled by python core.

    Development Note:
        - Not thoroughly tested for errors. There may be instances where this method may fail either to extract a valid archive or detect a corrupt archive.
        - Create custom exceptions.
        - Prevent overwriting files unless requested to do so.
        - Create a batch method.
    '''

    with open(src, 'rb') as f:
        sigver = f.read(8)
        unpacked_chunk = f.read(8)
        packed = f.read(8)
        unpacked = f.read(8)
        size_unpacked_chunk = struct.unpack('q', unpacked_chunk)[0]
        size_packed = struct.unpack('q', packed)[0]
        size_unpacked = struct.unpack('q', unpacked)[0]

        #Verify the integrity of the Archive Header
        if sigver == b'\xc1\x83\x2a\x9e\x00\x00\x00\x00' and isinstance(size_unpacked_chunk, int) and isinstance(size_packed , int) and isinstance(size_unpacked , int):
            logging.info(" archive is valid.")
            logging.debug(" archive header size information. Unpacked Chunk: {}({}) Full Packed: {}({}) Full Unpacked: {}({})".format(size_unpacked_chunk, unpacked_chunk, size_packed, packed, size_unpacked, unpacked))

            #Obtain the Archive Compression Index
            compression_index = []
            size_indexed = 0
            while size_indexed < size_unpacked:
                raw_compressed = f.read(8)
                raw_uncompressed = f.read(8)
                compressed = struct.unpack('q', raw_compressed)[0]
                uncompressed = struct.unpack('q', raw_uncompressed)[0]
                compression_index.append((compressed, uncompressed))
                size_indexed += uncompressed
                logging.debug("{}: {}/{} ({}/{}) - {} - {}".format(len(compression_index), size_indexed, size_unpacked, compressed, uncompressed, raw_compressed, raw_uncompressed))

            #Read the actual archive data
            data = b''
            read_data = 0
            for compressed, uncompressed in compression_index:
                compressed_data = f.read(compressed)
                uncompressed_data = zlib.decompress(compressed_data)
                if len(uncompressed_data) == uncompressed:
                    data += uncompressed_data
                    read_data += 1
                    if len(uncompressed_data) != size_unpacked_chunk and read_data != len(compression_index):
                        logging.critical(" archive is corrupt. Index contains more than one partial chunk: was {} when the full chunk size is {}, chunk {}/{}".format(len(uncompressed_data), size_unpacked_chunk, read_data, len(compression_index)))
                        exit(1)
                else:
                    logging.critical(" archive is corrupt. Uncompressed chunk size is not the same as in the index: was {} but should be {}.".format(len(uncompressed_data), size_uncompressed))
                    exit(2)
        else:
            logging.critical(" archive is not valid or corrupt. Either the signature and format version is incorrect or the header does not contain integers.")
            exit(3)

    with open(dst, 'wb') as f:
        f.write(data)
    logging.info(" archive has been extracted.")
