# CLIC Impact Scorecard pipeline

Research artefact of a master's thesis (design science research) carried out at CLIC Innovation Oy. The pipeline reads research and innovation proposal documents (PDF, 20 to 150 pages), extracts indicator fields with language models, validates them, passes them through human review and stores them in a relational database whose views feed CLIC's Impact Scorecard.

The repository holds two things:

1. **the software**: the pipeline, the pilot web interface and the evaluation harness;
2. **a replication package** of the evaluation that compares eleven language model configurations on ten documents with three repetitions each (330 runs): the documents, the reference records (gold sets), every run output and the results.

## Contents

| Path | What it is |
|---|---|
| `Second_step_CLICpipeline/clic_extract/` | extraction package: prompts, schema, model client, the eleven configurations, post processing |
| `src/pipeline/` | conversion (Docling), intake, database access, loading approved values, indicator queries |
| `src/evaluation/` | evaluation harness: batch runner, run storage, scorer, result tables and report |
| `webapp/` | pilot web interface (FastAPI) |
| `sdgautomation/` | local SDG suggestion (sentence embeddings), also usable as a stand alone service |
| `sql/schema.sql` | the database schema: pipeline layer, analytical star schema and indicator views |
| `tests/`, `Second_step_CLICpipeline/tests/` | tests, on fictional data only |
| `data/raw/`, `data/markdown/` | the evaluated documents, their Docling Markdown and conversion records (see "Data") |
| `evaluation/gold/` | the ten gold sets |
| `evaluation/runs/batch_20261030T105636Z/` | every file of the evaluated batch |
| `Final_Results/` | the evaluation package: method, final and first pass results, run record, discussion notes |
| `docs/` | database conceptual model and schema decisions |
| `provider_prices(1).csv` | the price list used for the cost of every run |

Start with `Final_Results/README.md` for the evaluation and `Final_Results/method/EVALUATION_PROTOCOL.md` for its method.

## How the pipeline works

1. **Upload.** A proposal PDF is uploaded in the web interface and stored.
2. **Document analysis.** Depending on the configuration, the model receives the Docling Markdown of the document, the page images, the embedded text with selected page images, or only pages selected by keyword rules. Every instruction ends with the same field definitions.
3. **Structured extraction.** The model answers under JSON schema enforcement, or as prose followed by one JSON block that Python extracts. Post processing converts amounts to integer cents and dates to ISO 8601, removes repeated partners, runs grounding and sum checks as warnings and validates the final record.
4. **Human approval.** A reviewer corrects the values, links each partner to the partner register and adds the fields that no proposal contains (decision, funding source, granted amounts).
5. **Storage.** Approved values are written to the SQLite database; views per indicator feed the Impact Scorecard.

Technology: Python 3.13; FastAPI, Jinja2 and Uvicorn on the server, HTMX, Tailwind CSS and Chart.js in the browser; Docling and PyMuPDF for documents; RapidOCR for the targeted configurations on scanned pages; rapidfuzz for partner matching; `sentence-transformers` and `scikit-learn` for SDG suggestions; SQLite through the standard library, in standard SQL. Models are called through the Hugging Face Inference Providers router; no model runs locally.

## The eleven configurations

| Configuration | Approach | Model | Provider | Answer |
|---|---|---|---|---|
| B | Text only | Qwen3.5 9B | deepinfra | schema enforced |
| C | Text only | gpt oss 120B | groq | schema enforced |
| D | Text only | gpt oss 20B | groq | schema enforced |
| freeform_B | Text only | Qwen3.5 9B | deepinfra | free form |
| freeform_light | Text only | Qwen3 4B Instruct | nscale | free form |
| multimodal_strict | Images only | Qwen3 VL 235B | deepinfra | schema enforced |
| multimodal_open | Images only | Qwen3 VL 235B | deepinfra | unconstrained |
| multimodal_combined_qwen_vl | Combined | Qwen3 VL 235B | deepinfra | unconstrained |
| multimodal_combined_llama4_maverick | Combined | Llama 4 Maverick | novita | unconstrained |
| targeted_text | Targeted | gpt oss 120B | groq | schema enforced |
| targeted_multimodal | Targeted | Qwen3 VL 235B | deepinfra | schema enforced |

Every setting, prompt and price of each configuration is in `Final_Results/method/EXTRACTION_CONFIGURATIONS.md` and in the run manifest. The prompts are in `Second_step_CLICpipeline/clic_extract/prompts.py`.

## Installation

Python 3.13 is required. From the repository root:

```
python -m venv .venv
.venv\Scripts\activate            # Windows; on Linux or macOS: source .venv/bin/activate
pip install -r requirements.txt
copy config.example.yaml config.yaml      # Linux or macOS: cp config.example.yaml config.yaml
python -m src.pipeline.db init
python -m src.pipeline.seed_sdgs
```

Model calls need a Hugging Face access token with permission to use Inference Providers. Put it in a file `.env` in the repository root, which is never committed:

```
HF_TOKEN=hf_...
```

Run the tests:

```
python -m pytest
cd Second_step_CLICpipeline && python -m pytest tests
```

## The pilot interface

The web interface is the tool meant for the pilot at CLIC: upload a proposal, choose one of the eleven configurations, review the extracted values with the suggested SDGs, complete and approve them, and see the projects, partners, dashboard and Impact Scorecard.

```
python -m uvicorn webapp.main:app --reload --port 8000
```

Then open http://127.0.0.1:8000. Text only configurations accept a PDF (converted with Docling first, which takes minutes on a laptop processor) or a converted `.md` file; all other configurations need the PDF.

**The evaluation was not run through the interface.** All 330 runs (eleven configurations, ten documents, three repetitions) were made with the command line batch runner (`src/evaluation/run_batch.py`), which calls the same configuration code and records every call, cost and time. The interface reuses that code for single documents.

Saving an approved proposal needs a partner register in the database. CLIC's real register is not published (see "Data"), so a fresh database has an empty one; load your own organisations into `dim_partner` before approving partners.

## Reproducing the evaluation

### 1. Check the reported figures

`Final_Results/EVALUATION_RESULTS.md` reports every figure with its source file. All of them can be recomputed from `Final_Results/results_second_pass_final/results_per_run.csv` (one row per run, every measure).

### 2. Rescore the batch, without calling any model

The published run files can be scored again exactly as for the thesis. Without the database (not published), the list of final runs is read from the batch's manifest and run files:

```
copy Final_Results\results_second_pass_final\review_decisions.csv evaluation\results\batch_20261030T105636Z\
python -m src.evaluation.score_batch --batch batch_20261030T105636Z --runs-from files
```

Create the folder `evaluation/results/batch_20261030T105636Z/` first. The scorer refuses to run on uncommitted code (add `--allow-dirty` to record it instead). It writes the results to `evaluation/results/batch_20261030T105636Z/` and a score file next to each run file; the results should equal those in `Final_Results/results_second_pass_final/` except for the scoring time and commit in the manifest. This holds for Abico_Synth too, although its Markdown is withheld: the scorer then reads `data/markdown/Abico_Synth.terms.json` (see "Data"), which gives exactly the same scores. Without `review_decisions.csv` the scorer gives the first pass (the automatic scoring with half scores, `Final_Results/results_first_pass/`). The scoring is deterministic and uses no language model.

### 3. Run the extraction again

```
python -m src.evaluation.convert_documents
python -m src.evaluation.run_batch --new --next 2
```

This calls the models and costs money (the evaluated batch cost USD 4.54). A new batch covers the nine published documents. Hosted inference is not fully deterministic even at temperature 0, and providers change their models and prices, so new runs reproduce the method, not the exact replies; the evaluated replies are published exactly as returned (`*.replies.json`).

## Versions used for the thesis

| Step | Tag | Commit |
|---|---|---|
| Runs of the evaluated batch (30 and 31 October 2026) | [`thesis-runs`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/thesis-runs) | [`1380dc7`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/1380dc76546f8846585b33d7337068e54683a213) |
| First pass scoring (31 October 2026) | [`thesis-first-pass`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/thesis-first-pass) | [`bc3d42b`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/bc3d42b70cb8bba066f287de0143eb8750aa806c) |
| Final scoring (9 November 2026) | [`thesis-scoring`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/thesis-scoring) | [`86e6d71`](https://github.com/Steve-Git9/CLIC_Scorecard_pipeline/tree/86e6d7108157d0fc48a654cafff7afef4447f088) |

Each link opens the repository as it was at that step. The tags are also listed under Tags on GitHub, and `git checkout thesis-runs` (or any other tag) gives the same code locally.

The extraction code (`Second_step_CLICpipeline/clic_extract/`) is unchanged since the runs. Each manifest records the commit that produced or scored it, with the digests of the prompts, the price file, the gold sets and the Markdown.

## Data

Nine of the ten documents are synthetic proposals; ByggMap is a proposal owned by the author. The gold sets were built by hand by the author. Amounts are stored as integer cents and dates as ISO 8601 text.

| Document | PDF and Markdown | Gold set, run outputs, results |
|---|---|---|
| ByggMap, CIRCUNOVA, CLIMACITIES, SP01, SP02, SP03A, SP03B, SP04, SP05 | published | published |
| Abico_Synth | **not published** | published |

**Abico_Synth** is synthetic, but the document still contains structures that are part of CLIC's internal knowledge. Its PDF and its Docling Markdown are therefore withheld; its gold set, its conversion record, every run output and every result are published, so all reported figures, Abico_Synth included, can be checked and rescored.

The scorer reads a document's Markdown for one purpose only: to check whether an extracted partner name, or a distinctive word of it, occurs in the document. For Abico_Synth these checks were made once on the Markdown, for every partner name any run extracted, and stored in `data/markdown/Abico_Synth.terms.json` (`python -m src.evaluation.document_terms`): names that are already in the run outputs, each with a yes or no, and no document text. With this file the scorer gives Abico_Synth exactly the same scores as with the Markdown itself.

Not published: the database (`data/clic.db`), the backups, two earlier batches stopped during development on an earlier document set, the pilot outputs, CLIC's partner register and the access token. The `.gitignore` is a whitelist: only the files named there are part of the repository.

## Environment as run

The steps of the evaluation ran on one Windows 11 laptop (AMD Ryzen 5 7520U, processor only):

1. **Docling conversion:** in the project environment (`.venv`, Python 3.13.2, Docling 2.130.0), on 30 October 2026.
2. **Batch run:** in the system Python 3.13 installation, which lacked the OCR package RapidOCR. As a result the six runs of the targeted configurations on the scanned document SP03B failed before any model call; they count as failures (`Final_Results/method/EVALUATION_PROTOCOL.md`, section 6.2).
3. **Scoring:** in the system Python 3.13 installation.

`requirements.txt` lists one environment with every package needed for all steps, at the versions of the project environment.

## Notes

1. `Second_step_CLICpipeline/clic_extract/evaluate.py` is the earlier scorer of the extraction package, still used by that package's tests; the evaluation uses `src/evaluation/`.
2. The Streamlit viewer used during development is not part of the repository; the web interface replaces it.
3. Paths are case sensitive on Linux and macOS: the folder is `Second_step_CLICpipeline`, with a capital S.

## Licence

Code: MIT licence (`LICENSE`). Documents, gold sets, run outputs and results: Creative Commons Attribution 4.0 International (`LICENSE-DATA.md`).

## Citation

See `CITATION.cff`, or use "Cite this repository" on the GitHub page.
