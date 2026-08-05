from PIL import Image
import sys


GFX_SIZE = 0x1800


# ----------------------------
# RLC DECOMPRESS
# ----------------------------

def rlc_decompress(data):
    out = bytearray(GFX_SIZE)

    i = 0
    p = 0
    n = len(data)

    while i < n:
        b = data[i]
        i += 1

        if b == 0:
            break

        if b & 0x80:
            count = b & 0x7f

            for _ in range(count):
                if i >= n:
                    break
                if p >= GFX_SIZE:
                    if p == GFX_SIZE + 1:
                        return out
                    p = 1

                out[p] = data[i]
                i += 1
                p += 2

        else:
            count = b
            value = data[i]
            i += 1

            for _ in range(count):
                if p >= GFX_SIZE:
                    if p == GFX_SIZE + 1:
                        return out
                    p = 1

                out[p] = value
                p += 2

    return out


# ----------------------------
# GB TILE -> PNG
# ----------------------------

def tiles_to_png(data, filename):

    width_tiles = 16
    height_tiles = len(data)//16//width_tiles

    img = Image.new(
        "L",
        (width_tiles*8, height_tiles*8)
    )

    px = img.load()


    for tile in range(width_tiles*height_tiles):

        base = tile*16

        tx = (tile % width_tiles)*8
        ty = (tile // width_tiles)*8

        for y in range(8):

            lo = data[base+y*2]
            hi = data[base+y*2+1]

            for x in range(8):

                bit = 7-x

                color = (
                    ((hi >> bit) & 1) << 1 |
                    ((lo >> bit) & 1)
                )

                px[tx+x, ty+y] = color*85


    img.save(filename)



# ----------------------------
# PNG -> GB TILE
# ----------------------------

def png_to_tiles(filename):

    img = Image.open(filename).convert("L")

    w,h = img.size

    tiles=[]

    for ty in range(0,h,8):
        for tx in range(0,w,8):

            tile=[]

            for y in range(8):

                lo=0
                hi=0

                for x in range(8):

                    v=img.getpixel((tx+x,ty+y))
                    v//=85

                    lo |= (v&1) << (7-x)
                    hi |= ((v>>1)&1) << (7-x)

                tile.append(lo)
                tile.append(hi)

            tiles.extend(tile)

    return bytearray(tiles)



# ----------------------------
# RLC COMPRESS
# ----------------------------

def interleave(data):

    half=len(data)//2

    return data[0::2]+data[1::2]



def rlc_compress(data):

    data=interleave(data)

    out=bytearray()

    i=0

    while i<len(data):

        run=1

        while (
            i+run<len(data)
            and data[i+run]==data[i]
            and run<0x7f
        ):
            run+=1


        if run>=3:
            out.append(run)
            out.append(data[i])
            i+=run

        else:

            start=i
            i+=1

            while (
                i<len(data)
                and i-start<0x7f
                and not (
                    i+2<len(data)
                    and data[i]==data[i+1]==data[i+2]
                )
            ):
                i+=1

            count=i-start

            out.append(count|0x80)
            out.extend(data[start:i])

    return out



# ----------------------------
# CLI
# ----------------------------

if __name__=="__main__":

    if sys.argv[1]=="decode":

        with open(sys.argv[2],"rb") as f:
            rlc=f.read()

        raw=rlc_decompress(rlc)

        tiles_to_png(raw,sys.argv[3])


    elif sys.argv[1]=="encode":

        raw=png_to_tiles(sys.argv[2])

        rlc=rlc_compress(raw)

        with open(sys.argv[3],"wb") as f:
            f.write(rlc)