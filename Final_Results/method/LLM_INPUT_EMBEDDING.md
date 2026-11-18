# How documents enter the language models

Status on 2 November 2026. Part 1 explains, in general terms, how a language model turns text and images into the numbers it works with (its embeddings). Part 2 explains how each of the eleven configurations of this project packs a proposal into the model call. Figures marked "measured" come from the full run, batch `batch_20261030T105636Z`. For the separate SDG classifier, see `SDG_EMBEDDING_MECHANISM.md`.

## Part 1. Inside the model

### 1.1 Text becomes tokens

A model does not read characters or words. Its tokenizer cuts the text into tokens: frequent words are one token, rarer words are split into pieces, and numbers, punctuation and spaces become tokens as well. Each model family has its own tokenizer, with a fixed vocabulary of tens of thousands to a few hundred thousand tokens, so the same text gives a different number of tokens per model.

Measured: in this project one input token corresponds to about 5.5 characters of the converted Markdown (median 5.4 for Qwen3.5 9B, 5.6 for gpt oss 120B). A 41 page proposal of about 129,000 characters is therefore about 23,000 tokens.

### 1.2 Tokens become embeddings

Every token in the vocabulary has a learned vector, its embedding: a long list of numbers (several thousand for the models tested) that the model learned during training so that tokens used in similar ways get similar vectors. The model looks up the vector of each input token. Information about the position of each token in the sequence is added, so that "partner A requests 100" and "100 requests partner A" are not the same input.

This is the only point where text "becomes numbers". From here on the model works on these vectors, not on text.

### 1.3 Images become tokens too

The vision models (Qwen3 VL 235B and Llama 4 Maverick) have an extra component, a vision encoder. It cuts each page image into a grid of small square patches, turns each patch into a vector, and compresses neighbouring patches into a smaller number of image tokens. A projection layer maps these image tokens into the same space as the text embeddings, and they are placed in the sequence where the image appears in the message. From then on the model treats text tokens and image tokens alike.

Measured: a page rendered at zoom 2.0 costs roughly 1,900 input tokens (estimated from the input token counts of multimodal_strict, after subtracting about 1,100 tokens of instructions per call). The same 41 page proposal sent as images is therefore about 78,000 tokens, more than three times its text. This is the main reason the image configurations cost more.

### 1.4 Processing and answering

The sequence of vectors passes through many transformer layers. In each layer every token can draw information from every other token (attention), so a partner name on page 30 can be linked to an amount in a table on page 45. The output is a probability for every possible next token. The model writes its answer one token at a time, each new token being appended to the sequence.

1. **Temperature 0.** All configurations ask for the most likely token at each step, which makes the answers as repeatable as the provider allows.
2. **Schema enforcement.** In the schema enforced configurations the provider removes, at every step, the tokens that would break the required JSON structure, so the answer is valid JSON of the required shape by construction. The free form configurations get no such help and write prose followed by a JSON block.

### 1.5 The context window

A model can hold only a limited number of tokens at once, input and output together: its context window. For the models tested it is 131,072 tokens (gpt oss 20B and 120B), 262,144 tokens (Qwen3.5 9B, Qwen3 4B, Qwen3 VL 235B) and 1,048,576 tokens (Llama 4 Maverick). Measured: every document fitted every text configuration's context in one call, the longest (146 pages) included.

### 1.6 What is not used

No retrieval with embeddings is used in the extraction: the document is not cut into pieces that are searched by similarity before the call. The model receives the whole text, or whole page images, or (in the targeted configurations) pages chosen by keyword rules, and does all the reading itself.

## Part 2. How each configuration feeds the model

All calls go through the Hugging Face Inference Providers service as chat messages: a system message with the instructions and the field definitions, and a user message with the document. Images are attached to the user message as PNG files encoded in base64.

| Approach | Configurations | What the model receives | Calls per document |
|---|---|---|---|
| Text only | B, C, D, freeform_B, freeform_light | the whole Docling Markdown of the document, inside `<document>` tags | one |
| Images only | multimodal_strict, multimodal_open | every page as a PNG image (zoom 2.0, about 144 dots per inch), in batches of 10 pages, each batch overlapping the previous one by 1 page | one per batch (a 45 page document: 5) |
| Combined | multimodal_combined_qwen_vl, multimodal_combined_llama4_maverick | the full text layer of the PDF (not the Docling Markdown), plus images of only the pages that contain a picture or a table, in batches of 10 with 1 page overlap; the full text is sent again with every batch | one per batch of images, at least one |
| Targeted | targeted_text, targeted_multimodal | at most 8 pages chosen locally by keyword rules, as text, plus tables parsed and checked arithmetically on the computer, plus identifier hints from the cover page; targeted_multimodal also attaches the images of up to 6 of those pages | one, plus one small page picking call when the keywords fail |

Notes:

1. **Batches are merged.** Where a document needs several calls, the partial answers are merged: for each single value field the first value found in page order, and the partner lists joined, with exact repeats removed.
2. **Splitting only when rejected.** Every input is first sent whole. Only if the provider rejects it as too large is it split in two and each half sent separately. Measured: text never needed splitting; page images were split only for the scanned document, whose pages make very large images.
3. **Two different text sources.** The text configurations read the Docling Markdown, which keeps table structure; the combined configurations read the plain text layer of the PDF, which does not, and rely on the images for tables.
4. **What the token counts mean for cost.** Text is the cheapest input per page, page images the most expensive, and the combined configurations pay for the full text again with every image batch.
