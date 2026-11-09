#!/usr/bin/env python3
"""Generate a lightweight additive 1.21.11 Minecraft resource pack for Santa's Tree Sword.
No Pillow, external downloads or unsigned binaries. Uses stdlib only.
"""
import hashlib
import io
import json
import struct
import zlib
import zipfile
from pathlib import Path

W,H=32,64
pix=[[(0,0,0,0) for _ in range(W)] for _ in range(H)]
def paint(x,y,rgb):
    if 0<=x<W and 0<=y<H:
        pix[y][x]=(*rgb,255)
def rect(x1,y1,x2,y2,col):
    for y in range(y1,y2+1):
        for x in range(x1,x2+1):paint(x,y,col)
def png_chunk(kind,data):
    return struct.pack("!I",len(data))+kind+data+struct.pack("!I",zlib.crc32(kind+data)&0xffffffff)

# trunk/handle: a large evergreen on an elegant brown sword hilt.
rect(14,40,17,60,(99,62,31))
rect(14,48,14,60,(144,93,45))
rect(12,55,19,57,(180,122,54))
rect(14,61,17,63,(208,168,78))
# tree outline and multiple stacked layers, with pixelated snow garlands.
for y in range(10,47):
    if y<22:radius=2+(y-10)//2
    elif y<35:radius=7+(y-22)//3
    else:radius=11+(y-35)//3
    radius=min(14,radius)
    for x in range(16-radius,17+radius):
        shade=(32,106,47) if (x+y)%5 else (41,134,55)
        if x==16-radius or x==16+radius:shade=(16,78,29)
        paint(x,y,shade)
# tiered branches shape, intentional chunky pine silhouette
for y in (22,34,45):
    for x in range(16-((y-10)//3+1),17+((y-10)//3+1)):
        if 0<=x<32:paint(x,y,(20,84,35))
# top star
for x,y in ((16,2),(16,3),(14,4),(15,4),(16,4),(17,4),(18,4),
            (16,5),(15,6),(17,6),(16,7)):
    paint(x,y,(250,215,70))
# ornaments and snowy sparkles
for i,(x,y) in enumerate([(13,20),(19,24),(9,32),(22,34),(12,39),
                          (25,40),(17,44),(6,43),(15,29),(23,45)]):
    paint(x,y,[(230,51,57),(253,201,66),(110,206,246),(236,170,231)][i%4])
for y in (18,27,36,43):
    radius=min(14,2+(y-10)//2 if y<22 else 7+(y-22)//3 if y<35 else 11+(y-35)//3)
    for x in range(16-radius+2,17+radius-1,3):
        paint(x,y+(x%2),(230,249,240))
# PNG RGBA data
raw=b"".join(b"\\x00"+b"".join(bytes(pixel) for pixel in row) for row in pix)
# convert escaped raw separator created by templating to actual zero byte
raw=b"".join(bytes([0])+b"".join(bytes(pixel) for pixel in row) for row in pix)
png=(b"\\x89PNG\\r\\n\\x1a\\n")
png=bytes.fromhex("89504e470d0a1a0a")
png+=png_chunk(b"IHDR",struct.pack("!IIBBBBB",W,H,8,6,0,0,0))
png+=png_chunk(b"IDAT",zlib.compress(raw,9))
png+=png_chunk(b"IEND",b"")
pack={"pack":{"description":"Crafted Horizons • Santa Tree Sword (Java 1.21.11)",
              "min_format":[75,0],"max_format":[75,0]}}
item={"model":{"type":"minecraft:model","model":"craftedhorizons:item/santa_tree_sword"}}
model={"parent":"minecraft:item/handheld",
       "textures":{"layer0":"craftedhorizons:item/santa_tree_sword"}}
out=Path("CHSantaSword-1.21.11.zip")
with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    z.writestr("pack.mcmeta",json.dumps(pack))
    z.writestr("assets/craftedhorizons/items/santa_tree_sword.json",json.dumps(item))
    z.writestr("assets/craftedhorizons/models/item/santa_tree_sword.json",json.dumps(model))
    z.writestr("assets/craftedhorizons/textures/item/santa_tree_sword.png",png)
data=out.read_bytes()
print("CHSantaSword pack bytes:",len(data))
print("SHA1:",hashlib.sha1(data).hexdigest())
print("SHA256:",hashlib.sha256(data).hexdigest())
Path("CHSantaSword-SHA1.txt").write_text(hashlib.sha1(data).hexdigest()+"  "+out.name+"\n")
