#!/bin/python

import sys
from pathlib import Path
from struct import unpack


def p3dz_decompress_chunk(in_bytes, verbose=False):
    def log(*args):
        if verbose:
            print(*args)

    out_bytes = bytearray()
    in_offset = 0
    out_offset = 0

    while in_offset < len(in_bytes):
        op_code = in_bytes[in_offset]
        in_offset += 1

        log(f"{op_code=}")

        if op_code < 16:
            log("copy from in_bytes")

            copy_size = op_code
            if copy_size == 0:
                copy_size += 15
                while in_bytes[in_offset] == 0:
                    copy_size += 255
                    in_offset += 1
                copy_size += in_bytes[in_offset]
                in_offset += 1

            log(f"  {copy_size=}")

            out_bytes.extend(in_bytes[in_offset : in_offset + copy_size])
            in_offset += copy_size
            out_offset += copy_size

        else:
            log("copy from out_bytes")

            copy_size = op_code % 16
            if copy_size == 0:
                copy_size += 15
                while in_bytes[in_offset] == 0:
                    copy_size += 255
                    in_offset += 1
                copy_size += in_bytes[in_offset]
                in_offset += 1

            copy_offset = len(out_bytes) - (int(op_code / 16) + (in_bytes[in_offset] * 16))
            in_offset += 1

            log(f"  {copy_size=}")
            log(f"  {copy_offset=}")

            out_bytes.extend(out_bytes[copy_offset : copy_offset + copy_size])
            out_offset += copy_size

            null_count = out_offset - len(out_bytes)
            log()
            log(f"  {null_count=}")
            out_bytes.extend([0] * null_count)

        log()
        log(f"  {in_offset=}")
        log(f"  {out_offset=}")
        log(f"  {len(out_bytes)=}")
        log()

    return out_bytes


def p3dz_decompress(path, verbose=False, verbose_chunks=False):
    def log(*args):
        if verbose:
            print(*args)

    log(f"decompressing {path}")

    path = Path(path)
    compressed_bytes = path.read_bytes()
    decompressed_bytes = bytearray()

    magic = compressed_bytes[:4]
    if magic != b"P3DZ":
        raise Exception(f"not a 'P3DZ' file, got '{magic}'")

    total_decompressed_size = unpack("I", compressed_bytes[4:8])[0]
    offset = 8

    log(f"{total_decompressed_size=}")

    already_decompressed_size = 0
    chunk_count = 0
    while already_decompressed_size < total_decompressed_size:
        chunk_count += 1
        log(f"  decompressing chunk {chunk_count}")
        
        chunk_compressed_size = unpack("I", compressed_bytes[offset : offset + 4])[0]
        offset += 4
        chunk_decompressed_size = unpack("I", compressed_bytes[offset : offset + 4])[0]
        offset += 4

        log(f"  {chunk_compressed_size=}")
        log(f"  {chunk_decompressed_size=}")

        chunk_compressed_bytes = compressed_bytes[offset : offset + chunk_compressed_size]
        offset += chunk_compressed_size

        decompressed_bytes.extend(p3dz_decompress_chunk(chunk_compressed_bytes, verbose_chunks))
        already_decompressed_size += chunk_decompressed_size

        log(f"  {already_decompressed_size=}")
        log()

    if len(decompressed_bytes) != total_decompressed_size:
        raise Exception(f"failed to decompress {path}")

    log(f"done decompressing")
    log()

    return decompressed_bytes


def p3dz_files(path):
    path = Path(path)
    result = list()
    for f in path.glob("**/*"):
        if f.is_file() and f.read_bytes()[:4] == b"P3DZ":
            result.append(f)
    return result


def p3dz_test_files(path, verbose=True, verbose_chunks=True):
    path = Path(path)
    for f in p3dz_files(path):
        print(f"testing {f.relative_to(path)}")
        p3dz_decompress(f, verbose, verbose_chunks)
    print("done")


def p3dz_decompress_files(path):
    path = Path(path)
    for f in p3dz_files(path):
        path_out = Path(f"{f}.decompressed")
        print(f"decompressed {path_out.relative_to(path)}")
        path_out.write_bytes(p3dz_decompress(f))
    print("done")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"usage: {sys.argv[0]} test|extract dir")
        print("  test: decompress any P3DZ files found in dir and its subdirs")
        print("  decompress: like test but save decompressed files as *.decompressed")
        exit()
    if sys.argv[1] == "test":
        verbose = len(sys.argv) > 3
        verbose_chunks = len(sys.argv) > 4
        p3dz_test_files(sys.argv[-1], verbose, verbose_chunks)
    elif sys.argv[1] == "decompress":
        p3dz_decompress_files(sys.argv[-1])
    else:
        print("doh")
