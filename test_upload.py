import asyncio
from fastapi import UploadFile
from io import BytesIO

async def main():
    f = UploadFile(file=BytesIO(b'hello'), filename='a.txt')
    c = await f.read()
    print('Content:', c)

if __name__ == '__main__':
    asyncio.run(main())
