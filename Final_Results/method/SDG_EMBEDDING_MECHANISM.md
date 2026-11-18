# How the SDG embedding mechanism works

Status on 2 November 2026. Code: `sdgautomation/sdg_core.py`, used by the review application (`webapp/main.py`) and by the stand alone service `sdgautomation/sdg_api.py`. This is the only part of the project that uses embeddings; elsewhere "embedded text" means the text layer stored inside a PDF.

## 1. Purpose

The mechanism suggests which of the 17 UN Sustainable Development Goals (SDGs) a proposal relates to. It is not done by the extraction models and is not part of the evaluation of the eleven configurations. It runs entirely on the local machine: no document text leaves it.

## 2. The idea in one paragraph

An embedding model turns a piece of text into a list of 384 numbers (a vector) such that texts with similar meaning get similar vectors. The mechanism turns a description of each SDG into a vector once, turns each part of the proposal into a vector, and measures how close they are. The SDGs whose descriptions are closest to the proposal's text are suggested.

## 3. Step by step

1. **Model.** `sentence-transformers/all-MiniLM-L6-v2`, a small, general purpose English sentence embedding model, downloaded once and then run locally on the processor. It produces vectors of 384 numbers and reads at most 256 tokens of a text (a token is a word or part of a word).
2. **SDG reference vectors.** `sdgautomation/sdgs.json` holds, for each of the 17 SDGs, its number, name, the official one line description and a longer "semantic profile" written for this project (what projects aligned with the goal typically do). Name, description and profile are joined into one text per SDG and turned into one vector each. This is done once when the classifier starts. Each of these texts is 186 to 251 tokens long, so the model reads all of it.
3. **Document chunks.** The proposal text is split into chunks of 500 words, one after the other, without overlap. In the review application the text is the converted Markdown of the proposal; the stand alone service reads the text of an uploaded PDF or Word file.
4. **Chunk vectors.** Each chunk is turned into a vector with the same model.
5. **Similarity.** For each chunk and each SDG, the cosine similarity of the two vectors is computed: a value that is higher the closer the two meanings are (in practice between about 0 and 1 for this model; 1 would be identical meaning).
6. **Two figures per SDG,** over all chunks of the document:
   1. **maximum similarity:** the highest similarity any single chunk reached with that SDG;
   2. **matching chunks:** the number of chunks whose similarity with that SDG is above 0.35.
7. **Score per SDG:**

   score = 0.8 × maximum similarity + 0.2 × min(matching chunks ÷ 5, 1)

   The best single passage counts for 80 %; how often the theme recurs counts for 20 %, and five or more matching chunks give the full 20 %.
8. **Result.** The 17 SDGs are sorted by score and the top five are returned, each with its score, maximum similarity and number of matching chunks.

**Worked example (invented numbers):** if the best chunk reaches 0.52 with SDG 7 and three chunks exceed 0.35, the score is 0.8 × 0.52 + 0.2 × 3 ÷ 5 = 0.416 + 0.12 = 0.536.

## 4. How the result is used

1. In the review application, the five suggested SDGs are shown in a panel next to the extracted fields while the reviewer checks a proposal.
2. When the reviewer approves the proposal, the five suggested SDGs are stored for it in the database (`fact_proposal_sdg`).
3. On the project page the reviewer can tick or untick SDGs; that list replaces the stored one. The suggestions are therefore a starting point for a human decision.
4. The results are cached per document while the application runs, so a document is classified only once.

## 5. Limitations

1. **Only part of each chunk is read.** The model reads at most 256 tokens, but a chunk of 500 words is about 830 tokens (median measured on one converted proposal). The model silently ignores the rest, so it reads roughly the first 150 words of every 500. About two thirds of the document's text never influences the result.
2. **Always five suggestions.** The top five are returned even when every score is low; the threshold of 0.35 is used only to count matching chunks, never to drop a weak SDG. A proposal clearly related to one or two goals still gets five suggestions.
3. **Fixed settings.** Chunk size (500 words), threshold (0.35), weights (0.8 and 0.2), the cap of five chunks and the number of suggestions (five) were set by judgement and have not been tuned or validated against reference SDG labels.
4. **General model.** The model is small and trained on general English text, not on research proposals; it measures similarity of wording and topic, not whether a project actually contributes to a goal.
5. **Not evaluated.** Unlike the extraction configurations, the SDG suggestions have no reference records and no accuracy figure; their quality rests on the reviewer's check.

## 6. Possible improvements

1. Make chunks fit the model: about 150 words per chunk, or a model that reads longer texts.
2. Return only SDGs above a score threshold, and at most five.
3. Build a small set of proposals with reference SDGs, chosen by the author, to tune the settings and measure accuracy.
