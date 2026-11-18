# Docling conversion speed on different hardware

Status on 31 October 2026. Question: the Docling conversion of the evaluation documents was slow on the author's laptop; would it be faster on better hardware, and by how much? This note compares the measured speed with published benchmarks. It changes nothing in the evaluation: all conversions of the batch were done once, on the machine described in section 1, and their times are the ones reported.

## 1. The machine and settings used

| Item | Value |
|---|---|
| Computer | Asus Vivobook Go E1504FA (laptop) |
| Processor | AMD Ryzen 5 7520U, 4 cores, 8 threads, 2.8 GHz |
| Memory | 15.3 GB |
| Graphics | AMD Radeon integrated graphics, 512 MB; not usable by Docling |
| Software | Windows 11, Python 3.13.2, Docling 2.130.0, PyTorch 2.14.0 CPU build (no CUDA) |
| Docling device | `auto`, which resolves to the processor, since no supported graphics card is present |
| Docling threads | 4 (the default) |
| Table structure | TableFormer in `accurate` mode (the default of this version), with cell matching |
| OCR | off, except for SP03B, the scanned copy |

Docling accelerates only on Nvidia graphics cards (CUDA), Apple processors (MPS) and Intel graphics (XPU); the list of devices in the installed version is `auto`, `cpu`, `cuda`, `mps`, `xpu`. AMD graphics are not among them, so on this laptop all work runs on the four processor cores.

## 2. Measured speed

From `data/markdown/conversions.csv` (conversion time proper, without start up and export):

| Set | Pages | Seconds | Seconds per page | Pages per second |
|---|---|---|---|---|
| Nine documents without OCR | 546 | 2,170 | 3.97 | 0.25 |
| SP03B, with OCR | 45 | 461 | 10.24 | 0.10 |
| All ten documents | 591 | 2,630 | 4.45 | 0.22 |

Per document the speed ranged from 2.56 seconds per page (CLIMACITIES, 2 tables) to 9.15 (ByggMap, 34 tables in 22 pages), so the number of tables matters more than the number of pages (section 2 of `CONVERSION_AND_DATA_CHECKS.md`).

## 3. Published figures

### 3.1 Docling paper, 2025 (Docling 2.5.2)

Livathinos, Auer and others, "Docling: An Efficient Open Source Toolkit for AI driven Document Conversion", arXiv 2501.17887, section 5.

1. Test set: 89 PDF files, 4,008 pages, 1,842 tables, 4,676 pictures.
2. Settings: OCR on (EasyOCR), TableFormer in `fast` mode, 8 threads on the processor.
3. Hardware: an AWS virtual machine with 8 virtual cores (AMD EPYC 7R13), 32 GB memory and an Nvidia L4 graphics card; and a MacBook Pro M3 Max with 64 GB.

| System | Mean seconds per page | Median seconds per page | 5th to 95th percentile |
|---|---|---|---|
| x86 processor, 8 threads | 3.1 | 0.79 | 0.6 to 16.3 |
| Apple M3 Max | 1.26 | 0.32 | 0.26 to 6.48 |
| Nvidia L4 graphics card | 0.48 | 0.114 | 0.057 to 2.08 |

The paper adds that disabling OCR saves 60 % of the time on the processors and 50 % on the graphics card, disabling table structure recognition saves 16 % and 24 %, and disabling both saves about 75 %.

### 3.2 Docling documentation, graphics card benchmarks (recent versions)

"GPU support" page of the Docling documentation. Test set: one PDF of 192 pages with 95 tables; standard pipeline, OCR off. The table mode and the exact Docling version are not stated.

| Hardware | Pages per second | Seconds per page |
|---|---|---|
| Desktop, Nvidia RTX 5090, AMD Ryzen 7 9800 (16 threads), Linux | 7.9 | 0.13 |
| Same desktop, processor only, 16 threads | 1.5 | 0.67 |
| Desktop, Nvidia RTX 5070, AMD Ryzen 7 9800 (16 threads), Windows 11 | 4.2 | 0.24 |
| Same desktop, processor only, 16 threads | 1.2 | 0.83 |
| AWS g6e.2xlarge, Nvidia L40S 48 GB, 8 virtual cores | 3.1 | 0.32 |

## 4. Comparison

The figures are not strictly comparable: the documents differ, the paper used OCR and the `fast` table mode, this project used no OCR (except SP03B) and the `accurate` mode, and the thread counts differ. The ratios below are therefore orders of magnitude, not predictions.

| Hardware | Seconds per page, without OCR | Times faster than this laptop (3.97) | Estimated time for the 546 pages without OCR |
|---|---|---|---|
| This laptop, 4 threads | 3.97 (measured) | 1 | 36 minutes (measured) |
| Server processor, 8 threads (paper, 3.1 with OCR, less 60 %) | about 1.2 | about 3 | about 11 minutes |
| Desktop processor, 16 threads (documentation) | 0.67 to 0.83 | about 5 to 6 | about 6 to 8 minutes |
| Apple M3 Max (paper, 1.26 with OCR, less 60 %) | about 0.5 | about 8 | about 5 minutes |
| Nvidia L40S, data centre card (documentation) | 0.32 | about 12 | about 3 minutes |
| Nvidia RTX 5070, desktop card (documentation) | 0.24 | about 16 | about 2 minutes |
| Nvidia RTX 5090, desktop card (documentation) | 0.13 | about 30 | about 1 minute |

## 5. Conclusions

1. **Yes, the conversion would be much faster on better hardware.** A desktop processor with more cores would be about five times faster; a computer with an Nvidia graphics card ten to thirty times faster. The 36 minutes of this batch would become a few minutes.
2. **The laptop is slow for three reasons:** it has only four cores, Docling used four threads, and its graphics are not supported by Docling. The `accurate` table mode, chosen for the quality of the partner and budget tables, adds to the time; the paper's figures were measured in the faster mode.
3. **OCR is the most expensive step.** SP03B took 2.6 times longer per page than the mean of the other documents, in line with the paper's statement that OCR is the costliest operation.
4. **Consequence for the evaluation.** The end to end time of the five text configurations includes the conversion, so their times depend on this hardware far more than on the models; on a machine with a graphics card the conversion part would shrink to seconds or a few minutes per document. This should be stated wherever their times are compared with the configurations that do not use Docling.
5. **Not tested here.** Speeding up the conversion on this laptop (more threads, the `fast` table mode) was not tried; the `fast` mode could change the converted tables and therefore the extraction results, so it is not a neutral change.

## Sources

1. Livathinos, N., Auer, C. and others (2025). Docling: An Efficient Open Source Toolkit for AI driven Document Conversion. arXiv 2501.17887. https://arxiv.org/abs/2501.17887
2. Docling documentation, GPU support. https://docling-project.github.io/docling/usage/gpu/
3. Local measurements: `data/markdown/conversions.csv` and the `<document>.conversion.json` records, 30 October 2026.
