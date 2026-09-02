# CY62167 transformed XY -> external address equations

All operations are exact over GF(2); bits are LSB-indexed.

```text
A0 = y4
A1 = y11
A2 = 1 xor x10 xor x11
A3 = 1 xor x9 xor x11
A4 = 1 xor x8 xor x11
A5 = 1 xor y10 xor y11
A6 = 1 xor x3 xor x8
A7 = y0
A8 = 1 xor x7 xor x8
A9 = 1 xor x2 xor x8
A10 = y8
A11 = y5
A12 = y6
A13 = y7
A14 = y3
A15 = y9
A16 = y2
A17 = y1
A18 = 1 xor x0 xor x8
A19 = 1 xor x1 xor x8
A20 = x11
```

Affine constant address at x=y=0: `787324`.
