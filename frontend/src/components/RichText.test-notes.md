# RichText image smoke test

Use the following content when manually testing the mobile question page:

`示意图：![平抛运动示意图](https://example.com/question.png)`

Expected behavior:

- only `http://`, `https://`, and root-relative `/...` image URLs render;
- the image is lazy-loaded and never exceeds the question card width;
- invalid schemes such as `javascript:` remain escaped text;
- existing inline and display KaTeX rendering remains unchanged.
