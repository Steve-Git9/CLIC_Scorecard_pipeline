# Spot check sample

Two final runs per configuration, drawn with the seed `spotcheck/batch_20261030T105636Z`. For each run: the scored fields beside the gold values, the partner entries with their classes, and the scores. Private file: it contains real names and values.

## B, SP03B, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\B\SP03B_20261030T132331Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | RESENSE | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | Adaptive Sensor Networks for Resource Efficient Process Monitoring | correct |
| proposal.call_identifier | RCF2027/6433 | RCF2027/6433 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 97930000 | 97930000 | correct |
| proposal_facts.trl_start | 3 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 1 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 1 |
| Kestrel Institute for Process Research | 24120000 | 0 |
| Ormenfield Process Systems Oy | 16710000 | 1 |
| Vantora Sensor Solutions Oy | 19640000 | 1 |
| Ostermark Regional Development Agency | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Torvenmaa University | 21480 | matched |  | wrong | same name |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980 | matched |  | wrong | same name |
| Kestrel Institute for ProcessResearch | null | supported_extra |  |  | name appears in the Docling Markdown |
| Ormenfield Process Systems Oy | null | matched |  | miss | same name |
| Vantora Sensor Solutions Oy | 19640 | matched |  | wrong | same name |
| Ostermark Regional Development Agency | 0 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980
    },
    {
      "partner_name": "Kestrel Institute for ProcessResearch",
      "requested_cents": null
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": null
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T13:23:31Z",
    "source_file": "SP03B.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## B, CIRCUNOVA, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\B\CIRCUNOVA_20261031T111352Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 6 (certain 6).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | CIRCUNOVA | CIRCUNOVA | correct |
| proposal.proposal_title | Circular Industry Networks for Regenerative Urban Materials | Circular Industry Networks for Regenerative Urban PVerials | wrong |
| proposal.call_identifier | HORIZON-CL6-2026-01-two-stage | HORIZON-CL6-2026-01-two-stage | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 600000000 | 600000000 | correct |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | 1 |
| VESTFJORD MUNICIPALITY | 25025000 | 1 |
| Vestfjord Enterprise Agency | 43000000 | 1 |
| Northbridge Materials ApS | 22237500 | 0 |
| Morrow Resource Recovery ApS | 20956250 | 0 |
| RenewLoop Denmark | 15837500 | 1 |
| LAKELAND REGIONAL COUNCIL | 14935000 | 1 |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | 1 |
| GREEN PATHWAYS OY | 43187500 | 1 |
| LAKELAND RESOURCE SERVICES OY | 33530000 | 1 |
| MineralCarbon Solutions Oy | 37975000 | 1 |
| TerraForm Innovations Oy | 38456250 | 1 |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | 1 |
| City of Valmont | 22406250 | 1 |
| EUROPEAN INSTITUTE OF MATERIALS | 21562500 | 0 |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | 1 |
| MUNICIPALITY OF PORTO VERDE | 22206250 | 1 |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | 1 |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | 1 |
| CycleReturn ApS | 0 | 1 |
| AFL | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | matched |  | correct | same name |
| VESTFJORD MUNICIPALITY | 25025000 | matched |  | correct | same name |
| Vestfjord Enterprise Agency | 43000000 | matched |  | correct | same name |
| Northbridge PVerials ApS | 22237500 | supported_extra |  |  | name appears in the Docling Markdown |
| Morrow Resource CRTNvery ApS | 20956250 | supported_extra |  |  | name appears in the Docling Markdown |
| RenewLoop Denmark | 15837500 | matched |  | correct | same name |
| LAKELAND REGIONAL COUNCIL | 14935000 | matched |  | correct | same name |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | matched |  | correct | same name |
| GREEN PATHWAYS OY | 43187500 | matched |  | correct | same name |
| LAKELAND RESOURCE SERVICES OY | 33530000 | matched |  | correct | same name |
| MineralCarbon Solutions Oy | 37975000 | matched |  | correct | same name |
| TerraForm Innovations Oy | 38456250 | matched |  | correct | same name |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | matched |  | correct | same name |
| City of Valmont | 22406250 | matched |  | correct | same name |
| EUROPEAN INSTITUTE OF PVERIALS | 21562500 | supported_extra |  |  | name appears in the Docling Markdown |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | matched |  | correct | same name |
| MUNICIPALITY OF PORTO VERDE | 22206250 | matched |  | correct | same name |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | matched |  | correct | same name |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | matched |  | correct | same name |
| CycleReturn ApS | null | matched |  | miss | same name |
| AFL | null | matched |  | miss | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban PVerials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge PVerials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource CRTNvery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF PVERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": null
    },
    {
      "partner_name": "AFL",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T11:13:52Z",
    "source_file": "CIRCUNOVA.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban Materials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge Materials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource Recovery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF MATERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "CIRCUNOVA_synthetic.pdf"
  }
}
```

</details>

## C, CLIMACITIES, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\C\CLIMACITIES_20261030T111339Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 1.0; errors 0 (certain 0).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | CLIMACITIES | CLIMACITIES | correct |
| proposal.proposal_title | Climate Intelligence for Equitable and Adaptive European Cities | Climate Intelligence for Equitable and Adaptive European Cities | correct |
| proposal.call_identifier | HORIZON-MISS-2027-CLIMA-SYN-01 | HORIZON-MISS-2027-CLIMA-SYN-01 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 750000000 | 750000000 | correct |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| NORDIC URBAN SYSTEMS INSTITUTE | 142000000 | 1 |
| RHEIN DATA LABS GMBH | 106000000 | 1 |
| ATLANTIC RESILIENCE CENTRE | 91000000 | 1 |
| CIVITAS ANALYTICS SL | 87000000 | 1 |
| DELTA WATER RESEARCH BV | 85000000 | 1 |
| BALTIC COMMUNITY LAB | 69000000 | 1 |
| ALPINE ENERGY INNOVATION SRL | 93000000 | 1 |
| URBAN FUTURES ASSOCIATION | 77000000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NORDIC URBAN SYSTEMS INSTITUTE | 142000000 | matched |  | correct | same name |
| RHEIN DATA LABS GMBH | 106000000 | matched |  | correct | same name |
| ATLANTIC RESILIENCE CENTRE | 91000000 | matched |  | correct | same name |
| CIVITAS ANALYTICS SL | 87000000 | matched |  | correct | same name |
| DELTA WATER RESEARCH BV | 85000000 | matched |  | correct | same name |
| BALTIC COMMUNITY LAB | 69000000 | matched |  | correct | same name |
| ALPINE ENERGY INNOVATION SRL | 93000000 | matched |  | correct | same name |
| URBAN FUTURES ASSOCIATION | 77000000 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "CLIMACITIES",
    "proposal_title": "Climate Intelligence for Equitable and Adaptive European Cities",
    "call_identifier": "HORIZON-MISS-2027-CLIMA-SYN-01",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 750000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC URBAN SYSTEMS INSTITUTE",
      "requested_cents": 142000000
    },
    {
      "partner_name": "RHEIN DATA LABS GMBH",
      "requested_cents": 106000000
    },
    {
      "partner_name": "ATLANTIC RESILIENCE CENTRE",
      "requested_cents": 91000000
    },
    {
      "partner_name": "CIVITAS ANALYTICS SL",
      "requested_cents": 87000000
    },
    {
      "partner_name": "DELTA WATER RESEARCH BV",
      "requested_cents": 85000000
    },
    {
      "partner_name": "BALTIC COMMUNITY LAB",
      "requested_cents": 69000000
    },
    {
      "partner_name": "ALPINE ENERGY INNOVATION SRL",
      "requested_cents": 93000000
    },
    {
      "partner_name": "URBAN FUTURES ASSOCIATION",
      "requested_cents": 77000000
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T11:13:39Z",
    "source_file": "CLIMACITIES.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "CLIMACITIES",
    "proposal_title": "Climate Intelligence for Equitable and Adaptive European Cities",
    "call_identifier": "HORIZON-MISS-2027-CLIMA-SYN-01",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 750000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC URBAN SYSTEMS INSTITUTE",
      "requested_cents": 142000000
    },
    {
      "partner_name": "RHEIN DATA LABS GMBH",
      "requested_cents": 106000000
    },
    {
      "partner_name": "ATLANTIC RESILIENCE CENTRE",
      "requested_cents": 91000000
    },
    {
      "partner_name": "CIVITAS ANALYTICS SL",
      "requested_cents": 87000000
    },
    {
      "partner_name": "DELTA WATER RESEARCH BV",
      "requested_cents": 85000000
    },
    {
      "partner_name": "BALTIC COMMUNITY LAB",
      "requested_cents": 69000000
    },
    {
      "partner_name": "ALPINE ENERGY INNOVATION SRL",
      "requested_cents": 93000000
    },
    {
      "partner_name": "URBAN FUTURES ASSOCIATION",
      "requested_cents": 77000000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "CLIMACITIES_Synthetic_Horizon_Proposal.pdf"
  }
}
```

</details>

## C, SP03B, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\C\SP03B_20261030T125647Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | RESENSE | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | Adaptive Sensor Networks for Resource Efficient Process Monitoring | correct |
| proposal.call_identifier | RCF2027/6433 | RCF2027/6433 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 97930000 | 97930000 | correct |
| proposal_facts.trl_start | 3 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 1 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 1 |
| Kestrel Institute for Process Research | 24120000 | 0 |
| Ormenfield Process Systems Oy | 16710000 | 1 |
| Vantora Sensor Solutions Oy | 19640000 | 1 |
| Ostermark Regional Development Agency | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Torvenmaa University | 21480 | matched |  | wrong | same name |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980 | matched |  | wrong | same name |
| Kestrel Institute for ProcessResearch | null | supported_extra |  |  | name appears in the Docling Markdown |
| Ormenfield Process Systems Oy | null | matched |  | miss | same name |
| Vantora Sensor Solutions Oy | 19640 | matched |  | wrong | same name |
| Ostermark Regional Development Agency | 0 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980
    },
    {
      "partner_name": "Kestrel Institute for ProcessResearch",
      "requested_cents": null
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": null
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T12:56:47Z",
    "source_file": "SP03B.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## D, SP03A, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\D\SP03A_20261030T145430Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 5 (certain 5).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | RESENSE | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | Adaptive Sensor Networks for Resource Efficient Process Monitoring | correct |
| proposal.call_identifier | RCF2027/6433 | RCF2027/6433 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 97930000 | null | miss |
| proposal_facts.trl_start | 3 | 3 | correct |
| proposal_facts.trl_target | 5 | 5 | correct |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 1 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 1 |
| Kestrel Institute for Process Research | 24120000 | 1 |
| Ormenfield Process Systems Oy | 16710000 | 1 |
| Vantora Sensor Solutions Oy | 19640000 | 1 |
| Ostermark Regional Development Agency | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Torvenmaa University | 21480 | matched |  | wrong | same name |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980 | matched |  | wrong | same name |
| Kestrel Institute for Process Research | 24120000 | matched |  | correct | same name |
| Ormenfield Process Systems Oy | 17780 | matched |  | wrong | same name |
| Vantora Sensor Solutions Oy | 19640 | matched |  | wrong | same name |
| Ostermark Regional Development Agency | 0 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": null,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 17780
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T14:54:30Z",
    "source_file": "SP03A.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## D, Abico_Synth, repetition 3

Run file `evaluation\runs\batch_20261030T105636Z\D\Abico_Synth_20261030T185117Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 4 (certain 4).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | ReCoSE | ReCoSE | correct |
| proposal.proposal_title | Renewable Composite Systems with Circular Engineering | Renewable Composite Systems with Circular Engineering ReCoSE | wrong |
| proposal.call_identifier | 7421_18_2026 | null | miss |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 221860000 | 386000000 | wrong |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Northern Lakes University of Applied Sciences | 48720000 | 0 |
| Lake District Technical University | 38240000 | 1 |
| Nordic Institute for Sustainable Materials | 64230000 | 1 |
| Eastern Nordic University | 36950000 | 1 |
| Coastal Finland University | 33720000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NLUAS University of Applied Science | 48720000 | supported_extra |  |  | name appears in the Docling Markdown |
| Lake District Technical University | 38240000 | matched |  | correct | same name |
| Nordic Institute for Sustainable Materials NISM | 64230000 | matched |  | correct | author's decision: gold:Nordic Institute for Sustainable Materials |
| Eastern Nordic University ENU | 36950000 | matched |  | correct | author's decision: gold:Eastern Nordic University |
| Coastal Finland University CFU | 33720000 | matched |  | correct | author's decision: gold:Coastal Finland University |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering ReCoSE",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 386000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NLUAS University of Applied Science",
      "requested_cents": 48720000
    },
    {
      "partner_name": "Lake District Technical University",
      "requested_cents": 38240000
    },
    {
      "partner_name": "Nordic Institute for Sustainable Materials NISM",
      "requested_cents": 64230000
    },
    {
      "partner_name": "Eastern Nordic University ENU",
      "requested_cents": 36950000
    },
    {
      "partner_name": "Coastal Finland University CFU",
      "requested_cents": 33720000
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T18:51:17Z",
    "source_file": "Abico_Synth.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering",
    "call_identifier": "7421_18_2026",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 221860000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Northern Lakes University of Applied Sciences",
      "requested_cents": 48720000
    },
    {
      "partner_name": "Lake District Technical University",
      "requested_cents": 38240000
    },
    {
      "partner_name": "Nordic Institute for Sustainable Materials",
      "requested_cents": 64230000
    },
    {
      "partner_name": "Eastern Nordic University",
      "requested_cents": 36950000
    },
    {
      "partner_name": "Coastal Finland University",
      "requested_cents": 33720000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "ABiCo_Synthetic_Confidentiality_Safe 4.docx"
  }
}
```

</details>

## freeform_B, ByggMap, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\freeform_B\ByggMap_20261031T075735Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 5 (certain 5).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | Bygg Map | Bygg Map | correct |
| proposal.proposal_title | Bygg Map | Bygg Map | correct |
| proposal.call_identifier | null | null | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 250000000 | 250000000 | correct |
| proposal_facts.trl_start | 4 | 4 | correct |
| proposal_facts.trl_target | 6 | 6 | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Management Center Innsbruck | 59062500 | 0 |
| Technical University of Cluj-Napoca | 46562500 | 0 |
| Norwegian University of Science and Technology | 74862500 | 0 |
| National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development | 20437500 | 0 |
| Sofia Municipality | 14437500 | 0 |
| CGI Suomi Oy | 19500000 | 1 |
| CEE Bankwatch | 15137500 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| MCI | 59062500 | supported_extra |  |  | name appears in the Docling Markdown |
| TUCN | 46562500 | supported_extra |  |  | name appears in the Docling Markdown |
| NTNU | 74862500 | supported_extra |  |  | name appears in the Docling Markdown |
| U-I | 20437500 | supported_extra |  |  | name appears in the Docling Markdown |
| SM | 14437500 | supported_extra |  |  | name appears in the Docling Markdown |
| CGI | 19500000 | matched |  | correct | author's decision: gold:CGI Suomi Oy |
| CEE | 15137500 | matched |  | correct | author's decision: gold:CEE Bankwatch |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "MCI",
      "requested_cents": 59062500
    },
    {
      "partner_name": "TUCN",
      "requested_cents": 46562500
    },
    {
      "partner_name": "NTNU",
      "requested_cents": 74862500
    },
    {
      "partner_name": "U-I",
      "requested_cents": 20437500
    },
    {
      "partner_name": "SM",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T07:57:35Z",
    "source_file": "ByggMap.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Management Center Innsbruck",
      "requested_cents": 59062500
    },
    {
      "partner_name": "Technical University of Cluj-Napoca",
      "requested_cents": 46562500
    },
    {
      "partner_name": "Norwegian University of Science and Technology",
      "requested_cents": 74862500
    },
    {
      "partner_name": "National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development",
      "requested_cents": 20437500
    },
    {
      "partner_name": "Sofia Municipality",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI Suomi Oy",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE Bankwatch",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## freeform_B, ByggMap, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\freeform_B\ByggMap_20261031T082035Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 6 (certain 6).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | Bygg Map | Bygg Map | correct |
| proposal.proposal_title | Bygg Map | Bygg Map is an innovative, data-driven platform designed to assess and map building energy efficiency across European cities at unprecedented scale and resolution. | wrong |
| proposal.call_identifier | null | null | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 250000000 | 250000000 | correct |
| proposal_facts.trl_start | 4 | 4 | correct |
| proposal_facts.trl_target | 6 | 6 | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Management Center Innsbruck | 59062500 | 0 |
| Technical University of Cluj-Napoca | 46562500 | 0 |
| Norwegian University of Science and Technology | 74862500 | 0 |
| National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development | 20437500 | 0 |
| Sofia Municipality | 14437500 | 0 |
| CGI Suomi Oy | 19500000 | 1 |
| CEE Bankwatch | 15137500 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| MCI | 59062500 | supported_extra |  |  | name appears in the Docling Markdown |
| TUCN | 46562500 | supported_extra |  |  | name appears in the Docling Markdown |
| NTNU | 74862500 | supported_extra |  |  | name appears in the Docling Markdown |
| U-I | 20437500 | supported_extra |  |  | name appears in the Docling Markdown |
| SM | 14437500 | supported_extra |  |  | name appears in the Docling Markdown |
| CGI | 19500000 | matched |  | correct | author's decision: gold:CGI Suomi Oy |
| CEE | 15137500 | matched |  | correct | author's decision: gold:CEE Bankwatch |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map is an innovative, data-driven platform designed to assess and map building energy efficiency across European cities at unprecedented scale and resolution.",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "MCI",
      "requested_cents": 59062500
    },
    {
      "partner_name": "TUCN",
      "requested_cents": 46562500
    },
    {
      "partner_name": "NTNU",
      "requested_cents": 74862500
    },
    {
      "partner_name": "U-I",
      "requested_cents": 20437500
    },
    {
      "partner_name": "SM",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T08:20:35Z",
    "source_file": "ByggMap.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Management Center Innsbruck",
      "requested_cents": 59062500
    },
    {
      "partner_name": "Technical University of Cluj-Napoca",
      "requested_cents": 46562500
    },
    {
      "partner_name": "Norwegian University of Science and Technology",
      "requested_cents": 74862500
    },
    {
      "partner_name": "National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development",
      "requested_cents": 20437500
    },
    {
      "partner_name": "Sofia Municipality",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI Suomi Oy",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE Bankwatch",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## freeform_light, SP02, repetition 3

Run file `evaluation\runs\batch_20261030T105636Z\freeform_light\SP02_20261030T185608Z.run.json`; status ok; valid at the first attempt False, after repair True; fully correct 0.0; errors 5 (certain 5).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | TIDEMESH | TIDEMESH | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resilient Coastal Infrastructure | Adaptive Sensor Networks for Resilient Coastal Infrastructure | correct |
| proposal.call_identifier | BF2026/93782 | BF2026/93782 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 99110000 | 99110000 | correct |
| proposal_facts.trl_start | 2 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Nordvalen Systems Oy | 18160000 | 1 |
| Kaltiora Analytics Oy | 19090000 | 1 |
| Lumenthar Marine Oy | 0 | 1 |
| Havrenmaa University | 25360000 | 1 |
| Taimerra Research Institute | 36500000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Nordvalen Systems Oy (NVS) | 18160000 | matched |  | correct | author's decision: gold:Nordvalen Systems Oy |
| Kaltiora Analytics Oy (KTA) | 19090000 | matched |  | correct | author's decision: gold:Kaltiora Analytics Oy |
| Lumenthar Marine Oy (LMR) | null | matched |  | miss | author's decision: gold:Lumenthar Marine Oy |
| Havrenmaa University (HVU) | null | matched |  | miss | author's decision: gold:Havrenmaa University |
| Taimerra Research Institute (TMI) | null | matched |  | miss | author's decision: gold:Taimerra Research Institute |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "TIDEMESH",
    "proposal_title": "Adaptive Sensor Networks for Resilient Coastal Infrastructure",
    "call_identifier": "BF2026/93782",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 99110000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Nordvalen Systems Oy (NVS)",
      "requested_cents": 18160000
    },
    {
      "partner_name": "Kaltiora Analytics Oy (KTA)",
      "requested_cents": 19090000
    },
    {
      "partner_name": "Lumenthar Marine Oy (LMR)",
      "requested_cents": null
    },
    {
      "partner_name": "Havrenmaa University (HVU)",
      "requested_cents": null
    },
    {
      "partner_name": "Taimerra Research Institute (TMI)",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T18:56:08Z",
    "source_file": "SP02.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "TIDEMESH",
    "proposal_title": "Adaptive Sensor Networks for Resilient Coastal Infrastructure",
    "call_identifier": "BF2026/93782",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 99110000,
    "trl_start": 2,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Nordvalen Systems Oy",
      "requested_cents": 18160000
    },
    {
      "partner_name": "Kaltiora Analytics Oy",
      "requested_cents": 19090000
    },
    {
      "partner_name": "Lumenthar Marine Oy",
      "requested_cents": 0
    },
    {
      "partner_name": "Havrenmaa University",
      "requested_cents": 25360000
    },
    {
      "partner_name": "Taimerra Research Institute",
      "requested_cents": 36500000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "SP02.pdf"
  }
}
```

</details>

## freeform_light, SP03B, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\freeform_light\SP03B_20261030T132315Z.run.json`; status ok; valid at the first attempt False, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | RESENSE | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | Adaptive Sensor Networks for Resource Efficient Process Monitoring | correct |
| proposal.call_identifier | RCF2027/6433 | RCF2027/6433 | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 97930000 | 97930000 | correct |
| proposal_facts.trl_start | 3 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 1 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 1 |
| Kestrel Institute for Process Research | 24120000 | 1 |
| Ormenfield Process Systems Oy | 16710000 | 1 |
| Vantora Sensor Solutions Oy | 19640000 | 1 |
| Ostermark Regional Development Agency | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Torvenmaa University | 21480 | matched |  | wrong | same name |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980 | matched |  | wrong | same name |
| Kestrel Institute for Process Research | null | matched |  | miss | same name |
| Ormenfield Process Systems Oy | null | matched |  | miss | same name |
| Vantora Sensor Solutions Oy | 19640 | matched |  | wrong | same name |
| Ostermark Regional Development Agency | 0 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": null
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": null
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T13:23:15Z",
    "source_file": "SP03B.md"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## multimodal_combined_llama4_maverick, SP04, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_combined_llama4_maverick\SP04_20261031T073708Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | MAROFLOW | MAROFLOW | correct |
| proposal.proposal_title | Marine Observation Flows for Shared Coastal Planning | Marine Observation Flows for Shared Coastal Planning | correct |
| proposal.call_identifier | BSR2026C41 | BSR2026C41 | correct |
| proposal.submission_date | 2026-08-10 | 2026-08-10 | correct |
| proposal_facts.requested_total_cents | 294610000 | 294610000 | correct |
| proposal_facts.trl_start | 3 | 3 | correct |
| proposal_facts.trl_target | 6 | 6 | correct |
| proposal_facts.mcrl_start | 4 | 4 | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Hallvik University | 67450000 | 1 |
| Orrenfjord Marine Systems Ltd | 56880000 | 1 |
| Marovik Research Institute | 59280000 | 1 |
| Quenmark Sensor Works Ltd | 50700000 | 1 |
| Ostrelund Regional Development Agency | 21300000 | 1 |
| Brenvik Port Logistics Ltd | 0 | 1 |
| Eskeby Technical University | 39000000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Hallvik University | 67450 | matched |  | wrong | same name |
| Orrenfjord Marine Systems Ltd | 56880 | matched |  | wrong | same name |
| Marovik Research Institute | 59280 | matched |  | wrong | same name |
| Quenmark Sensor Works Ltd | 50700 | matched |  | wrong | same name |
| Ostrelund Regional Development Agency | 21300 | matched |  | wrong | same name |
| Brenvik Port Logistics Ltd | 0 | matched |  | correct | same name |
| Eskeby Technical University | null | matched |  | miss | same name |
| Orrenfjord Marine Systems Ltd (formerly Kellmar Technologies Ltd) | 56880 | duplicate |  |  | author's decision: gold:Orrenfjord Marine Systems Ltd |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "MAROFLOW",
    "proposal_title": "Marine Observation Flows for Shared Coastal Planning",
    "call_identifier": "BSR2026C41",
    "submission_date": "2026-08-10"
  },
  "proposal_facts": {
    "requested_total_cents": 294610000,
    "trl_start": 3,
    "trl_target": 6,
    "mcrl_start": 4,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Hallvik University",
      "requested_cents": 67450
    },
    {
      "partner_name": "Orrenfjord Marine Systems Ltd",
      "requested_cents": 56880
    },
    {
      "partner_name": "Marovik Research Institute",
      "requested_cents": 59280
    },
    {
      "partner_name": "Quenmark Sensor Works Ltd",
      "requested_cents": 50700
    },
    {
      "partner_name": "Ostrelund Regional Development Agency",
      "requested_cents": 21300
    },
    {
      "partner_name": "Brenvik Port Logistics Ltd",
      "requested_cents": 0
    },
    {
      "partner_name": "Eskeby Technical University",
      "requested_cents": null
    },
    {
      "partner_name": "Orrenfjord Marine Systems Ltd (formerly Kellmar Technologies Ltd)",
      "requested_cents": 56880
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T07:37:08Z",
    "source_file": "SP04.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "MAROFLOW",
    "proposal_title": "Marine Observation Flows for Shared Coastal Planning",
    "call_identifier": "BSR2026C41",
    "submission_date": "2026-08-10"
  },
  "proposal_facts": {
    "requested_total_cents": 294610000,
    "trl_start": 3,
    "trl_target": 6,
    "mcrl_start": 4,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Hallvik University",
      "requested_cents": 67450000
    },
    {
      "partner_name": "Orrenfjord Marine Systems Ltd",
      "requested_cents": 56880000
    },
    {
      "partner_name": "Marovik Research Institute",
      "requested_cents": 59280000
    },
    {
      "partner_name": "Quenmark Sensor Works Ltd",
      "requested_cents": 50700000
    },
    {
      "partner_name": "Ostrelund Regional Development Agency",
      "requested_cents": 21300000
    },
    {
      "partner_name": "Brenvik Port Logistics Ltd",
      "requested_cents": 0
    },
    {
      "partner_name": "Eskeby Technical University",
      "requested_cents": 39000000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## multimodal_combined_llama4_maverick, Abico_Synth, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_combined_llama4_maverick\Abico_Synth_20261030T181019Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | ReCoSE | ReCoSE | correct |
| proposal.proposal_title | Renewable Composite Systems with Circular Engineering | Renewable Composite Systems with Circular Engineering ReCoSE | wrong |
| proposal.call_identifier | 7421_18_2026 | null | miss |
| proposal.submission_date | null | 2026-03-01 | unsupported |
| proposal_facts.requested_total_cents | 221860000 | 221860000 | correct |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Northern Lakes University of Applied Sciences | 48720000 | 0 |
| Lake District Technical University | 38240000 | 1 |
| Nordic Institute for Sustainable Materials | 64230000 | 0 |
| Eastern Nordic University | 36950000 | 0 |
| Coastal Finland University | 33720000 | 0 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NLUAS | 48720000 | supported_extra |  |  | name appears in the Docling Markdown |
| Lake District Technical University | 38240000 | matched |  | correct | same name |
| NISM | 64230000 | supported_extra |  |  | name appears in the Docling Markdown |
| ENU | 36950000 | supported_extra |  |  | name appears in the Docling Markdown |
| CFU | 33720000 | supported_extra |  |  | name appears in the Docling Markdown |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering ReCoSE",
    "call_identifier": null,
    "submission_date": "2026-03-01"
  },
  "proposal_facts": {
    "requested_total_cents": 221860000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NLUAS",
      "requested_cents": 48720000
    },
    {
      "partner_name": "Lake District Technical University",
      "requested_cents": 38240000
    },
    {
      "partner_name": "NISM",
      "requested_cents": 64230000
    },
    {
      "partner_name": "ENU",
      "requested_cents": 36950000
    },
    {
      "partner_name": "CFU",
      "requested_cents": 33720000
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T18:10:19Z",
    "source_file": "Abico_Synth.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering",
    "call_identifier": "7421_18_2026",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 221860000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Northern Lakes University of Applied Sciences",
      "requested_cents": 48720000
    },
    {
      "partner_name": "Lake District Technical University",
      "requested_cents": 38240000
    },
    {
      "partner_name": "Nordic Institute for Sustainable Materials",
      "requested_cents": 64230000
    },
    {
      "partner_name": "Eastern Nordic University",
      "requested_cents": 36950000
    },
    {
      "partner_name": "Coastal Finland University",
      "requested_cents": 33720000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "ABiCo_Synthetic_Confidentiality_Safe 4.docx"
  }
}
```

</details>

## multimodal_combined_qwen_vl, ByggMap, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_combined_qwen_vl\ByggMap_20261031T075307Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 3 (certain 3).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | Bygg Map | Bygg Map | correct |
| proposal.proposal_title | Bygg Map | Bygg Map is an innovative, data-driven platform designed to assess and map building energy efficiency across European cities at unprecedented scale and resolution. | wrong |
| proposal.call_identifier | null | null | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 250000000 | 250000000 | correct |
| proposal_facts.trl_start | 4 | 4 | correct |
| proposal_facts.trl_target | 6 | 6 | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Management Center Innsbruck | 59062500 | 1 |
| Technical University of Cluj-Napoca | 46562500 | 1 |
| Norwegian University of Science and Technology | 74862500 | 1 |
| National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development | 20437500 | 1 |
| Sofia Municipality | 14437500 | 1 |
| CGI Suomi Oy | 19500000 | 1 |
| CEE Bankwatch | 15137500 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Management Center Innsbruck - Austria | 59062500 | matched |  | correct | author's decision: gold:Management Center Innsbruck |
| Technical University of Cluj-Napoca - Romania | 46562500 | matched |  | correct | author's decision: gold:Technical University of Cluj-Napoca |
| Norwegian University of Science and Technology - Norway | 74862500 | matched |  | correct | author's decision: gold:Norwegian University of Science and Technology |
| National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development - Romania | 20437500 | matched |  | correct | author's decision: gold:National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development |
| Sofia Municipality - Bulgaria | 14437500 | matched |  | correct | author's decision: gold:Sofia Municipality |
| CGI Suomi Oy - Finland | 19500000 | matched |  | correct | author's decision: gold:CGI Suomi Oy |
| CEE Bankwatch – Czech Republic | 15137500 | matched |  | correct | author's decision: gold:CEE Bankwatch |
| MCI | 59062500 | supported_extra |  |  | name appears in the Docling Markdown |
| TUCN | 46562500 | supported_extra |  |  | name appears in the Docling Markdown |
| NTNU | 74862500 | supported_extra |  |  | name appears in the Docling Markdown |
| U-I | 20437500 | supported_extra |  |  | name appears in the Docling Markdown |
| SM | 14437500 | supported_extra |  |  | name appears in the Docling Markdown |
| CGI | 19500000 | duplicate |  |  | fragment of a gold partner that is already matched |
| CEE | 15137500 | duplicate |  |  | fragment of a gold partner that is already matched |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map is an innovative, data-driven platform designed to assess and map building energy efficiency across European cities at unprecedented scale and resolution.",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Management Center Innsbruck - Austria",
      "requested_cents": 59062500
    },
    {
      "partner_name": "Technical University of Cluj-Napoca - Romania",
      "requested_cents": 46562500
    },
    {
      "partner_name": "Norwegian University of Science and Technology - Norway",
      "requested_cents": 74862500
    },
    {
      "partner_name": "National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development - Romania",
      "requested_cents": 20437500
    },
    {
      "partner_name": "Sofia Municipality - Bulgaria",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI Suomi Oy - Finland",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE Bankwatch – Czech Republic",
      "requested_cents": 15137500
    },
    {
      "partner_name": "MCI",
      "requested_cents": 59062500
    },
    {
      "partner_name": "TUCN",
      "requested_cents": 46562500
    },
    {
      "partner_name": "NTNU",
      "requested_cents": 74862500
    },
    {
      "partner_name": "U-I",
      "requested_cents": 20437500
    },
    {
      "partner_name": "SM",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T07:53:07Z",
    "source_file": "ByggMap.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "Bygg Map",
    "proposal_title": "Bygg Map",
    "call_identifier": null,
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 250000000,
    "trl_start": 4,
    "trl_target": 6,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Management Center Innsbruck",
      "requested_cents": 59062500
    },
    {
      "partner_name": "Technical University of Cluj-Napoca",
      "requested_cents": 46562500
    },
    {
      "partner_name": "Norwegian University of Science and Technology",
      "requested_cents": 74862500
    },
    {
      "partner_name": "National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development",
      "requested_cents": 20437500
    },
    {
      "partner_name": "Sofia Municipality",
      "requested_cents": 14437500
    },
    {
      "partner_name": "CGI Suomi Oy",
      "requested_cents": 19500000
    },
    {
      "partner_name": "CEE Bankwatch",
      "requested_cents": 15137500
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## multimodal_combined_qwen_vl, CIRCUNOVA, repetition 3

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_combined_qwen_vl\CIRCUNOVA_20261031T133347Z.run.json`; status ok; valid at the first attempt False, after repair True; fully correct 0.0; errors 9 (certain 9).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | CIRCUNOVA | CIRCUNOVA | correct |
| proposal.proposal_title | Circular Industry Networks for Regenerative Urban Materials | Circular Industry Networks for Regenerative Urban PVerials | wrong |
| proposal.call_identifier | HORIZON-CL6-2026-01-two-stage | HORIZON-CL6-2026-01-two-stage | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 600000000 | 600000000 | correct |
| proposal_facts.trl_start | null | 4 | unsupported |
| proposal_facts.trl_target | null | 7 | unsupported |
| proposal_facts.mcrl_start | null | 3 | unsupported |
| proposal_facts.mcrl_target | null | 6 | unsupported |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | 1 |
| VESTFJORD MUNICIPALITY | 25025000 | 1 |
| Vestfjord Enterprise Agency | 43000000 | 1 |
| Northbridge Materials ApS | 22237500 | 0 |
| Morrow Resource Recovery ApS | 20956250 | 0 |
| RenewLoop Denmark | 15837500 | 1 |
| LAKELAND REGIONAL COUNCIL | 14935000 | 1 |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | 1 |
| GREEN PATHWAYS OY | 43187500 | 1 |
| LAKELAND RESOURCE SERVICES OY | 33530000 | 1 |
| MineralCarbon Solutions Oy | 37975000 | 1 |
| TerraForm Innovations Oy | 38456250 | 1 |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | 1 |
| City of Valmont | 22406250 | 1 |
| EUROPEAN INSTITUTE OF MATERIALS | 21562500 | 0 |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | 1 |
| MUNICIPALITY OF PORTO VERDE | 22206250 | 1 |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | 1 |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | 1 |
| CycleReturn ApS | 0 | 1 |
| AFL | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | matched |  | correct | same name |
| VESTFJORD MUNICIPALITY | 25025000 | matched |  | correct | same name |
| Vestfjord Enterprise Agency | 43000000 | matched |  | correct | same name |
| Northbridge PVerials ApS | 22237500 | supported_extra |  |  | name appears in the Docling Markdown |
| Morrow Resource CRTNvery ApS | 20956250 | supported_extra |  |  | name appears in the Docling Markdown |
| RenewLoop Denmark | 15837500 | matched |  | correct | same name |
| LAKELAND REGIONAL COUNCIL | 14935000 | matched |  | correct | same name |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | matched |  | correct | same name |
| GREEN PATHWAYS OY | 43187500 | matched |  | correct | same name |
| LAKELAND RESOURCE SERVICES OY | 33530000 | matched |  | correct | same name |
| MineralCarbon Solutions Oy | 37975000 | matched |  | correct | same name |
| TerraForm Innovations Oy | 38456250 | matched |  | correct | same name |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | matched |  | correct | same name |
| City of Valmont | 22406250 | matched |  | correct | same name |
| EUROPEAN INSTITUTE OF PVERIALS | 21562500 | supported_extra |  |  | name appears in the Docling Markdown |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | matched |  | correct | same name |
| MUNICIPALITY OF PORTO VERDE | 22206250 | matched |  | correct | same name |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | matched |  | correct | same name |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | matched |  | correct | same name |
| CycleReturn ApS | 0 | matched |  | correct | same name |
| AFL | 0 | matched |  | correct | same name |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINES TAMPERE OY | 30325000 | unsupported_extra |  |  | author's decision: unsupported_extra |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban PVerials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": 4,
    "trl_target": 7,
    "mcrl_start": 3,
    "mcrl_target": 6
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge PVerials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource CRTNvery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF PVERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINES TAMPERE OY",
      "requested_cents": 30325000
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T13:33:47Z",
    "source_file": "CIRCUNOVA.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban Materials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge Materials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource Recovery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF MATERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "CIRCUNOVA_synthetic.pdf"
  }
}
```

</details>

## multimodal_open, Abico_Synth, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_open\Abico_Synth_20261030T165553Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 12 (certain 12).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | ReCoSE | ReCoSE | correct |
| proposal.proposal_title | Renewable Composite Systems with Circular Engineering | Renewable Composite Systems with Circular Engineering ReCoSE | wrong |
| proposal.call_identifier | 7421_18_2026 | HORIZON-CL5-2026-D3-01 | wrong |
| proposal.submission_date | null | 2026-01-15 | unsupported |
| proposal_facts.requested_total_cents | 221860000 | 221860000 | correct |
| proposal_facts.trl_start | null | 3 | unsupported |
| proposal_facts.trl_target | null | 5 | unsupported |
| proposal_facts.mcrl_start | null | 2 | unsupported |
| proposal_facts.mcrl_target | null | 4 | unsupported |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Northern Lakes University of Applied Sciences | 48720000 | 0 |
| Lake District Technical University | 38240000 | 0 |
| Nordic Institute for Sustainable Materials | 64230000 | 1 |
| Eastern Nordic University | 36950000 | 1 |
| Coastal Finland University | 33720000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NISM | null | supported_extra |  |  | name appears in the Docling Markdown |
| NLUAS | null | supported_extra |  |  | name appears in the Docling Markdown |
| LDTU | null | supported_extra |  |  | name appears in the Docling Markdown |
| ENU | null | supported_extra |  |  | name appears in the Docling Markdown |
| CFU | null | supported_extra |  |  | name appears in the Docling Markdown |
| NLUAS University of Applied Science | null | supported_extra |  |  | name appears in the Docling Markdown |
| LDTU University (LDTU) | null | supported_extra |  |  | name appears in the Docling Markdown |
| Nordic Institute for Sustainable Materials NISM | null | matched |  | miss | author's decision: gold:Nordic Institute for Sustainable Materials |
| Eastern Nordic University ENU | null | matched |  | miss | author's decision: gold:Eastern Nordic University |
| Coastal Finland University CFU | null | matched |  | miss | author's decision: gold:Coastal Finland University |
| PolyCycle | null | supported_extra |  |  | name appears in the Docling Markdown |
| NorthGrid Energy WS | null | supported_extra |  |  | name appears in the Docling Markdown |
| ForestLoop Fibre | null | supported_extra |  |  | name appears in the Docling Markdown |
| CircuForm | null | supported_extra |  |  | name appears in the Docling Markdown |
| BioCoat Solutions | null | supported_extra |  |  | name appears in the Docling Markdown |
| NordWindow Group | null | supported_extra |  |  | name appears in the Docling Markdown |
| Atmosense | null | supported_extra |  |  | name appears in the Docling Markdown |
| Aurora Shipworks | null | supported_extra |  |  | name appears in the Docling Markdown |
| PolyNova Labs | null | supported_extra |  |  | name appears in the Docling Markdown |
| SurfaceTech Nordic | null | supported_extra |  |  | name appears in the Docling Markdown |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering ReCoSE",
    "call_identifier": "HORIZON-CL5-2026-D3-01",
    "submission_date": "2026-01-15"
  },
  "proposal_facts": {
    "requested_total_cents": 221860000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 2,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "NISM",
      "requested_cents": null
    },
    {
      "partner_name": "NLUAS",
      "requested_cents": null
    },
    {
      "partner_name": "LDTU",
      "requested_cents": null
    },
    {
      "partner_name": "ENU",
      "requested_cents": null
    },
    {
      "partner_name": "CFU",
      "requested_cents": null
    },
    {
      "partner_name": "NLUAS University of Applied Science",
      "requested_cents": null
    },
    {
      "partner_name": "LDTU University (LDTU)",
      "requested_cents": null
    },
    {
      "partner_name": "Nordic Institute for Sustainable Materials NISM",
      "requested_cents": null
    },
    {
      "partner_name": "Eastern Nordic University ENU",
      "requested_cents": null
    },
    {
      "partner_name": "Coastal Finland University CFU",
      "requested_cents": null
    },
    {
      "partner_name": "PolyCycle",
      "requested_cents": null
    },
    {
      "partner_name": "NorthGrid Energy WS",
      "requested_cents": null
    },
    {
      "partner_name": "ForestLoop Fibre",
      "requested_cents": null
    },
    {
      "partner_name": "CircuForm",
      "requested_cents": null
    },
    {
      "partner_name": "BioCoat Solutions",
      "requested_cents": null
    },
    {
      "partner_name": "NordWindow Group",
      "requested_cents": null
    },
    {
      "partner_name": "Atmosense",
      "requested_cents": null
    },
    {
      "partner_name": "Aurora Shipworks",
      "requested_cents": null
    },
    {
      "partner_name": "PolyNova Labs",
      "requested_cents": null
    },
    {
      "partner_name": "SurfaceTech Nordic",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T16:55:53Z",
    "source_file": "Abico_Synth.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "ReCoSE",
    "proposal_title": "Renewable Composite Systems with Circular Engineering",
    "call_identifier": "7421_18_2026",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 221860000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Northern Lakes University of Applied Sciences",
      "requested_cents": 48720000
    },
    {
      "partner_name": "Lake District Technical University",
      "requested_cents": 38240000
    },
    {
      "partner_name": "Nordic Institute for Sustainable Materials",
      "requested_cents": 64230000
    },
    {
      "partner_name": "Eastern Nordic University",
      "requested_cents": 36950000
    },
    {
      "partner_name": "Coastal Finland University",
      "requested_cents": 33720000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "ABiCo_Synthetic_Confidentiality_Safe 4.docx"
  }
}
```

</details>

## multimodal_open, CIRCUNOVA, repetition 1

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_open\CIRCUNOVA_20261031T111414Z.run.json`; status ok; valid at the first attempt False, after repair True; fully correct 0.0; errors 24 (certain 24).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | CIRCUNOVA | CIRCUNOVA | correct |
| proposal.proposal_title | Circular Industry Networks for Regenerative Urban Materials | Circular Industry Networks for Regenerative Urban PVerials | wrong |
| proposal.call_identifier | HORIZON-CL6-2026-01-two-stage | HORIZON-CL6-2026-01-CIRCBIO-02-two-stage | wrong |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 600000000 | 600000000 | correct |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | 1 |
| VESTFJORD MUNICIPALITY | 25025000 | 1 |
| Vestfjord Enterprise Agency | 43000000 | 1 |
| Northbridge Materials ApS | 22237500 | 0 |
| Morrow Resource Recovery ApS | 20956250 | 0 |
| RenewLoop Denmark | 15837500 | 1 |
| LAKELAND REGIONAL COUNCIL | 14935000 | 1 |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | 1 |
| GREEN PATHWAYS OY | 43187500 | 1 |
| LAKELAND RESOURCE SERVICES OY | 33530000 | 1 |
| MineralCarbon Solutions Oy | 37975000 | 1 |
| TerraForm Innovations Oy | 38456250 | 1 |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | 1 |
| City of Valmont | 22406250 | 1 |
| EUROPEAN INSTITUTE OF MATERIALS | 21562500 | 0 |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | 1 |
| MUNICIPALITY OF PORTO VERDE | 22206250 | 1 |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | 1 |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | 1 |
| CycleReturn ApS | 0 | 1 |
| AFL | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | null | matched |  | miss | same name |
| VESTFJORD MUNICIPALITY | null | matched |  | miss | same name |
| Vestfjord Enterprise Agency | null | matched |  | miss | same name |
| Northbridge PVerials ApS | null | supported_extra |  |  | name appears in the Docling Markdown |
| Morrow Resource CRTNvery ApS | null | supported_extra |  |  | name appears in the Docling Markdown |
| ReneeLoop Denmark | null | unsupported_extra |  |  | author's decision: unsupported_extra |
| LAKELAND REGIONAL COUNCIL | null | matched |  | miss | same name |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | null | matched |  | miss | same name |
| GREEN PATHWAYS OY | null | matched |  | miss | same name |
| LAKELAND RESOURCE SERVICES OY | null | matched |  | miss | same name |
| MineralCarbon Solutions Oy | null | matched |  | miss | same name |
| TerraForm Innovations Oy | null | matched |  | miss | same name |
| BALTIC INSTITUTE OF TECHNOLOGY | null | matched |  | miss | same name |
| City of Valmont | null | matched |  | miss | same name |
| EUROPEAN INSTITUTE OF PVERIALS | null | supported_extra |  |  | name appears in the Docling Markdown |
| AEGEAN REGIONAL INNOVATION FUND | null | matched |  | miss | same name |
| MUNICIPALITY OF PORTO VERDE | null | matched |  | miss | same name |
| UNIVERSITY OF HARZ TECHNOLOGY | null | matched |  | miss | same name |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | null | matched |  | miss | same name |
| CycleReturn ApS | null | matched |  | miss | same name |
| AFL | null | matched |  | miss | same name |
| RenewLoop Denmark | null | matched |  | miss | same name |
| NCS | 66670000 | supported_extra |  |  | name appears in the Docling Markdown |
| VEST | 25025000 | supported_extra |  |  | name appears in the Docling Markdown |
| VEA | 43000000 | supported_extra |  |  | name appears in the Docling Markdown |
| NBM | 22237500 | supported_extra |  |  | name appears in the Docling Markdown |
| MRR | 20956250 | supported_extra |  |  | name appears in the Docling Markdown |
| LRC | 14935000 | supported_extra |  |  | name appears in the Docling Markdown |
| LBDA | 30325000 | supported_extra |  |  | name appears in the Docling Markdown |
| GPO | 43187500 | supported_extra |  |  | name appears in the Docling Markdown |
| LRS | 33530000 | supported_extra |  |  | name appears in the Docling Markdown |
| MCS | 37975000 | supported_extra |  |  | name appears in the Docling Markdown |
| TFI | 38456250 | supported_extra |  |  | name appears in the Docling Markdown |
| BIT | 36650000 | supported_extra |  |  | name appears in the Docling Markdown |
| VALM | 22406250 | supported_extra |  |  | name appears in the Docling Markdown |
| EIM | 21562500 | supported_extra |  |  | name appears in the Docling Markdown |
| ARIF | 13587500 | supported_extra |  |  | name appears in the Docling Markdown |
| PV | 22206250 | supported_extra |  |  | name appears in the Docling Markdown |
| UHT | 57150000 | supported_extra |  |  | name appears in the Docling Markdown |
| SUAS | 34302500 | supported_extra |  |  | name appears in the Docling Markdown |
| CRTN | null | supported_extra |  |  | name appears in the Docling Markdown |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban PVerials",
    "call_identifier": "HORIZON-CL6-2026-01-CIRCBIO-02-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": null
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": null
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": null
    },
    {
      "partner_name": "Northbridge PVerials ApS",
      "requested_cents": null
    },
    {
      "partner_name": "Morrow Resource CRTNvery ApS",
      "requested_cents": null
    },
    {
      "partner_name": "ReneeLoop Denmark",
      "requested_cents": null
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": null
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": null
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": null
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": null
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": null
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": null
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": null
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": null
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF PVERIALS",
      "requested_cents": null
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": null
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": null
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": null
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": null
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": null
    },
    {
      "partner_name": "AFL",
      "requested_cents": null
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": null
    },
    {
      "partner_name": "NCS",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VEST",
      "requested_cents": 25025000
    },
    {
      "partner_name": "VEA",
      "requested_cents": 43000000
    },
    {
      "partner_name": "NBM",
      "requested_cents": 22237500
    },
    {
      "partner_name": "MRR",
      "requested_cents": 20956250
    },
    {
      "partner_name": "LRC",
      "requested_cents": 14935000
    },
    {
      "partner_name": "LBDA",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GPO",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LRS",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MCS",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TFI",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BIT",
      "requested_cents": 36650000
    },
    {
      "partner_name": "VALM",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EIM",
      "requested_cents": 21562500
    },
    {
      "partner_name": "ARIF",
      "requested_cents": 13587500
    },
    {
      "partner_name": "PV",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UHT",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SUAS",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CRTN",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T11:14:14Z",
    "source_file": "CIRCUNOVA.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban Materials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge Materials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource Recovery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF MATERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "CIRCUNOVA_synthetic.pdf"
  }
}
```

</details>

## multimodal_strict, SP02, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_strict\SP02_20261030T175447Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 7 (certain 7).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | TIDEMESH | TIDEMESH | correct |
| proposal.proposal_title | Adaptive Sensor Networks for Resilient Coastal Infrastructure | Adaptive Sensor Networks for Resilient Coastal Infrastructure | correct |
| proposal.call_identifier | BF2026/93782 | BF2026/93782 | correct |
| proposal.submission_date | null | 2026-04-02 | unsupported |
| proposal_facts.requested_total_cents | 99110000 | 200340000 | wrong |
| proposal_facts.trl_start | 2 | 2 | correct |
| proposal_facts.trl_target | 5 | 5 | correct |
| proposal_facts.mcrl_start | 1 | 1 | correct |
| proposal_facts.mcrl_target | 4 | 4 | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Nordvalen Systems Oy | 18160000 | 1 |
| Kaltiora Analytics Oy | 19090000 | 1 |
| Lumenthar Marine Oy | 0 | 1 |
| Havrenmaa University | 25360000 | 1 |
| Taimerra Research Institute | 36500000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NVS | null | supported_extra |  |  | name appears in the Docling Markdown |
| KTA | null | supported_extra |  |  | name appears in the Docling Markdown |
| LMR | null | supported_extra |  |  | name appears in the Docling Markdown |
| HVU | null | supported_extra |  |  | name appears in the Docling Markdown |
| TMI | null | supported_extra |  |  | name appears in the Docling Markdown |
| Nordvalen Systems Oy (NVS) | 23000000 | matched |  | wrong | author's decision: gold:Nordvalen Systems Oy |
| Kaltiora Analytics Oy (KTA) | null | matched |  | miss | author's decision: gold:Kaltiora Analytics Oy |
| Lumenthar Marine Oy (LMR) | null | matched |  | miss | author's decision: gold:Lumenthar Marine Oy |
| Havrenmaa University (HVU) | null | matched |  | miss | author's decision: gold:Havrenmaa University |
| Taimerra Research Institute (TMI) | null | matched |  | miss | author's decision: gold:Taimerra Research Institute |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "TIDEMESH",
    "proposal_title": "Adaptive Sensor Networks for Resilient Coastal Infrastructure",
    "call_identifier": "BF2026/93782",
    "submission_date": "2026-04-02"
  },
  "proposal_facts": {
    "requested_total_cents": 200340000,
    "trl_start": 2,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "NVS",
      "requested_cents": null
    },
    {
      "partner_name": "KTA",
      "requested_cents": null
    },
    {
      "partner_name": "LMR",
      "requested_cents": null
    },
    {
      "partner_name": "HVU",
      "requested_cents": null
    },
    {
      "partner_name": "TMI",
      "requested_cents": null
    },
    {
      "partner_name": "Nordvalen Systems Oy (NVS)",
      "requested_cents": 23000000
    },
    {
      "partner_name": "Kaltiora Analytics Oy (KTA)",
      "requested_cents": null
    },
    {
      "partner_name": "Lumenthar Marine Oy (LMR)",
      "requested_cents": null
    },
    {
      "partner_name": "Havrenmaa University (HVU)",
      "requested_cents": null
    },
    {
      "partner_name": "Taimerra Research Institute (TMI)",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T17:54:47Z",
    "source_file": "SP02.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "TIDEMESH",
    "proposal_title": "Adaptive Sensor Networks for Resilient Coastal Infrastructure",
    "call_identifier": "BF2026/93782",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 99110000,
    "trl_start": 2,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Nordvalen Systems Oy",
      "requested_cents": 18160000
    },
    {
      "partner_name": "Kaltiora Analytics Oy",
      "requested_cents": 19090000
    },
    {
      "partner_name": "Lumenthar Marine Oy",
      "requested_cents": 0
    },
    {
      "partner_name": "Havrenmaa University",
      "requested_cents": 25360000
    },
    {
      "partner_name": "Taimerra Research Institute",
      "requested_cents": 36500000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "SP02.pdf"
  }
}
```

</details>

## multimodal_strict, SP04, repetition 3

Run file `evaluation\runs\batch_20261030T105636Z\multimodal_strict\SP04_20261031T084836Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 15 (certain 15).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | MAROFLOW | MAROFLOW | correct |
| proposal.proposal_title | Marine Observation Flows for Shared Coastal Planning | Marine Observation Flows for Shared Coastal Planning | correct |
| proposal.call_identifier | BSR2026C41 | BSR2026C41 | correct |
| proposal.submission_date | 2026-08-10 | 2026-08-10 | correct |
| proposal_facts.requested_total_cents | 294610000 | 320750000 | wrong |
| proposal_facts.trl_start | 3 | 3 | correct |
| proposal_facts.trl_target | 6 | 6 | correct |
| proposal_facts.mcrl_start | 4 | 4 | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Hallvik University | 67450000 | 1 |
| Orrenfjord Marine Systems Ltd | 56880000 | 1 |
| Marovik Research Institute | 59280000 | 1 |
| Quenmark Sensor Works Ltd | 50700000 | 1 |
| Ostrelund Regional Development Agency | 21300000 | 1 |
| Brenvik Port Logistics Ltd | 0 | 1 |
| Eskeby Technical University | 39000000 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Hallvik University | null | matched |  | miss | same name |
| Orrenfjord Marine Systems Ltd (formerly Kellmar Technologies Ltd) | null | matched |  | miss | author's decision: gold:Orrenfjord Marine Systems Ltd |
| Marovik Research Institute | null | matched |  | miss | same name |
| Quenmark Sensor Works Ltd | null | matched |  | miss | same name |
| Ostrelund Regional Development Agency | null | matched |  | miss | same name |
| Brenvik Port Logistics Ltd | null | matched |  | miss | same name |
| Eskeby Technical University | null | matched |  | miss | same name |
| Hallvik | 81970000 | duplicate |  |  | fragment of a gold partner that is already matched |
| Kellmar | 67470000 | supported_extra |  |  | name appears in the Docling Markdown |
| Marovik | 62140000 | duplicate |  |  | fragment of a gold partner that is already matched |
| Quenmark | 53970000 | duplicate |  |  | fragment of a gold partner that is already matched |
| Ostrelund | 19350000 | duplicate |  |  | fragment of a gold partner that is already matched |
| Brenvik | 0 | duplicate |  |  | fragment of a gold partner that is already matched |
| Lindmark | 35850000 | supported_extra |  |  | name appears in the Docling Markdown |
| Orrenfjord | 56880 | duplicate |  |  | fragment of a gold partner that is already matched |
| Eskeby | null | duplicate |  |  | fragment of a gold partner that is already matched |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "MAROFLOW",
    "proposal_title": "Marine Observation Flows for Shared Coastal Planning",
    "call_identifier": "BSR2026C41",
    "submission_date": "2026-08-10"
  },
  "proposal_facts": {
    "requested_total_cents": 320750000,
    "trl_start": 3,
    "trl_target": 6,
    "mcrl_start": 4,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Hallvik University",
      "requested_cents": null
    },
    {
      "partner_name": "Orrenfjord Marine Systems Ltd (formerly Kellmar Technologies Ltd)",
      "requested_cents": null
    },
    {
      "partner_name": "Marovik Research Institute",
      "requested_cents": null
    },
    {
      "partner_name": "Quenmark Sensor Works Ltd",
      "requested_cents": null
    },
    {
      "partner_name": "Ostrelund Regional Development Agency",
      "requested_cents": null
    },
    {
      "partner_name": "Brenvik Port Logistics Ltd",
      "requested_cents": null
    },
    {
      "partner_name": "Eskeby Technical University",
      "requested_cents": null
    },
    {
      "partner_name": "Hallvik",
      "requested_cents": 81970000
    },
    {
      "partner_name": "Kellmar",
      "requested_cents": 67470000
    },
    {
      "partner_name": "Marovik",
      "requested_cents": 62140000
    },
    {
      "partner_name": "Quenmark",
      "requested_cents": 53970000
    },
    {
      "partner_name": "Ostrelund",
      "requested_cents": 19350000
    },
    {
      "partner_name": "Brenvik",
      "requested_cents": 0
    },
    {
      "partner_name": "Lindmark",
      "requested_cents": 35850000
    },
    {
      "partner_name": "Orrenfjord",
      "requested_cents": 56880
    },
    {
      "partner_name": "Eskeby",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T08:48:36Z",
    "source_file": "SP04.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "MAROFLOW",
    "proposal_title": "Marine Observation Flows for Shared Coastal Planning",
    "call_identifier": "BSR2026C41",
    "submission_date": "2026-08-10"
  },
  "proposal_facts": {
    "requested_total_cents": 294610000,
    "trl_start": 3,
    "trl_target": 6,
    "mcrl_start": 4,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Hallvik University",
      "requested_cents": 67450000
    },
    {
      "partner_name": "Orrenfjord Marine Systems Ltd",
      "requested_cents": 56880000
    },
    {
      "partner_name": "Marovik Research Institute",
      "requested_cents": 59280000
    },
    {
      "partner_name": "Quenmark Sensor Works Ltd",
      "requested_cents": 50700000
    },
    {
      "partner_name": "Ostrelund Regional Development Agency",
      "requested_cents": 21300000
    },
    {
      "partner_name": "Brenvik Port Logistics Ltd",
      "requested_cents": 0
    },
    {
      "partner_name": "Eskeby Technical University",
      "requested_cents": 39000000
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## targeted_multimodal, SP03B, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\targeted_multimodal\SP03B_20261030T134408Z.run.json`; status failed; valid at the first attempt False, after repair False; fully correct 0.0; errors 15 (certain 15).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | null | miss |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | null | miss |
| proposal.call_identifier | RCF2027/6433 | null | miss |
| proposal.submission_date | null | null | miss |
| proposal_facts.requested_total_cents | 97930000 | null | miss |
| proposal_facts.trl_start | 3 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | null | miss |
| proposal_facts.mcrl_target | 4 | null | miss |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 0 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 0 |
| Kestrel Institute for Process Research | 24120000 | 0 |
| Ormenfield Process Systems Oy | 16710000 | 0 |
| Vantora Sensor Solutions Oy | 19640000 | 0 |
| Ostermark Regional Development Agency | 0 | 0 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|

<details><summary>Final record and gold set (JSON)</summary>

```json
null
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## targeted_multimodal, SP03B, repetition 3

Run file `evaluation\runs\batch_20261030T105636Z\targeted_multimodal\SP03B_20261030T161450Z.run.json`; status failed; valid at the first attempt False, after repair False; fully correct 0.0; errors 15 (certain 15).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | RESENSE | null | miss |
| proposal.proposal_title | Adaptive Sensor Networks for Resource Efficient Process Monitoring | null | miss |
| proposal.call_identifier | RCF2027/6433 | null | miss |
| proposal.submission_date | null | null | miss |
| proposal_facts.requested_total_cents | 97930000 | null | miss |
| proposal_facts.trl_start | 3 | null | miss |
| proposal_facts.trl_target | 5 | null | miss |
| proposal_facts.mcrl_start | 1 | null | miss |
| proposal_facts.mcrl_target | 4 | null | miss |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Torvenmaa University | 21480000 | 0 |
| Haldeberg University of Applied Sciences and Regional Innovation Services | 15980000 | 0 |
| Kestrel Institute for Process Research | 24120000 | 0 |
| Ormenfield Process Systems Oy | 16710000 | 0 |
| Vantora Sensor Solutions Oy | 19640000 | 0 |
| Ostermark Regional Development Agency | 0 | 0 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|

<details><summary>Final record and gold set (JSON)</summary>

```json
null
```

```json
{
  "proposal": {
    "proposal_acronym": "RESENSE",
    "proposal_title": "Adaptive Sensor Networks for Resource Efficient Process Monitoring",
    "call_identifier": "RCF2027/6433",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 97930000,
    "trl_start": 3,
    "trl_target": 5,
    "mcrl_start": 1,
    "mcrl_target": 4
  },
  "partners": [
    {
      "partner_name": "Torvenmaa University",
      "requested_cents": 21480000
    },
    {
      "partner_name": "Haldeberg University of Applied Sciences and Regional Innovation Services",
      "requested_cents": 15980000
    },
    {
      "partner_name": "Kestrel Institute for Process Research",
      "requested_cents": 24120000
    },
    {
      "partner_name": "Ormenfield Process Systems Oy",
      "requested_cents": 16710000
    },
    {
      "partner_name": "Vantora Sensor Solutions Oy",
      "requested_cents": 19640000
    },
    {
      "partner_name": "Ostermark Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## targeted_text, SP01, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\targeted_text\SP01_20261030T114931Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 9 (certain 9).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | LOOPWEAVE | LOOPWEAVE | correct |
| proposal.proposal_title | Circular Weaving of Recycled Fibre Value Chains | Circular Weaving of Recycled Fibre Value Chains | correct |
| proposal.call_identifier | INNO-2027-03-CIRCFIBRE-04 | INNO-2027-03-CIRCFIBRE-04 | correct |
| proposal.submission_date | 2027-03-06 | 2027-03-06 | correct |
| proposal_facts.requested_total_cents | 478980000 | 478980000 | correct |
| proposal_facts.trl_start | 5 | 5 | correct |
| proposal_facts.trl_target | 7 | null | miss |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| Kalevra Innovation Cluster Oy | 57560000 | 1 |
| Northbay Materials Oy | 46660000 | 1 |
| Corvane Polymer Systems AB | 57800000 | 1 |
| Tessilo Process Engineering GmbH | 55210000 | 1 |
| Rauvik University | 64390000 | 1 |
| Elvaris University of Technology | 73590000 | 1 |
| Sundmark Applied Research Institute | 55320000 | 1 |
| Brenvik Institute for Sustainable Process Engineering | 68450000 | 1 |
| Lindfors Regional Development Agency | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| Kalevra Innovation Cluster Oy | 57560 | matched |  | wrong | same name |
| Northbay Materials Oy | 46660 | matched |  | wrong | same name |
| Corvane Polymer Systems AB | 57800 | matched |  | wrong | same name |
| Tessilo Process Engineering GmbH | 55210000 | matched |  | correct | same name |
| Rauvik University | null | matched |  | miss | same name |
| Elvaris University of Technology | null | matched |  | miss | same name |
| Sundmark Applied Research Institute | null | matched |  | miss | same name |
| Brenvik Institute for Sustainable Process Engineering | null | matched |  | miss | same name |
| Lindfors Regional Development Agency | null | matched |  | miss | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "LOOPWEAVE",
    "proposal_title": "Circular Weaving of Recycled Fibre Value Chains",
    "call_identifier": "INNO-2027-03-CIRCFIBRE-04",
    "submission_date": "2027-03-06"
  },
  "proposal_facts": {
    "requested_total_cents": 478980000,
    "trl_start": 5,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Kalevra Innovation Cluster Oy",
      "requested_cents": 57560
    },
    {
      "partner_name": "Northbay Materials Oy",
      "requested_cents": 46660
    },
    {
      "partner_name": "Corvane Polymer Systems AB",
      "requested_cents": 57800
    },
    {
      "partner_name": "Tessilo Process Engineering GmbH",
      "requested_cents": 55210000
    },
    {
      "partner_name": "Rauvik University",
      "requested_cents": null
    },
    {
      "partner_name": "Elvaris University of Technology",
      "requested_cents": null
    },
    {
      "partner_name": "Sundmark Applied Research Institute",
      "requested_cents": null
    },
    {
      "partner_name": "Brenvik Institute for Sustainable Process Engineering",
      "requested_cents": null
    },
    {
      "partner_name": "Lindfors Regional Development Agency",
      "requested_cents": null
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-30T11:49:31Z",
    "source_file": "SP01.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "LOOPWEAVE",
    "proposal_title": "Circular Weaving of Recycled Fibre Value Chains",
    "call_identifier": "INNO-2027-03-CIRCFIBRE-04",
    "submission_date": "2027-03-06"
  },
  "proposal_facts": {
    "requested_total_cents": 478980000,
    "trl_start": 5,
    "trl_target": 7,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "Kalevra Innovation Cluster Oy",
      "requested_cents": 57560000
    },
    {
      "partner_name": "Northbay Materials Oy",
      "requested_cents": 46660000
    },
    {
      "partner_name": "Corvane Polymer Systems AB",
      "requested_cents": 57800000
    },
    {
      "partner_name": "Tessilo Process Engineering GmbH",
      "requested_cents": 55210000
    },
    {
      "partner_name": "Rauvik University",
      "requested_cents": 64390000
    },
    {
      "partner_name": "Elvaris University of Technology",
      "requested_cents": 73590000
    },
    {
      "partner_name": "Sundmark Applied Research Institute",
      "requested_cents": 55320000
    },
    {
      "partner_name": "Brenvik Institute for Sustainable Process Engineering",
      "requested_cents": 68450000
    },
    {
      "partner_name": "Lindfors Regional Development Agency",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": null
  }
}
```

</details>

## targeted_text, CIRCUNOVA, repetition 2

Run file `evaluation\runs\batch_20261030T105636Z\targeted_text\CIRCUNOVA_20261031T125549Z.run.json`; status ok; valid at the first attempt True, after repair True; fully correct 0.0; errors 21 (certain 21).

| Field | Gold | Extracted | Outcome |
|---|---|---|---|
| proposal.proposal_acronym | CIRCUNOVA | CIRCUNOVA | correct |
| proposal.proposal_title | Circular Industry Networks for Regenerative Urban Materials | Circular Industry Networks for Regenerative Urban PVerials | wrong |
| proposal.call_identifier | HORIZON-CL6-2026-01-two-stage | HORIZON-CL6-2026-01-two-stage | correct |
| proposal.submission_date | null | null | correct |
| proposal_facts.requested_total_cents | 600000000 | 600000000 | correct |
| proposal_facts.trl_start | null | null | correct |
| proposal_facts.trl_target | null | null | correct |
| proposal_facts.mcrl_start | null | null | correct |
| proposal_facts.mcrl_target | null | null | correct |

| Gold partner | Gold amount (cents) | Found |
|---|---|---|
| NORDIC CIRCULAR SYSTEMS OY | 66670000 | 0 |
| VESTFJORD MUNICIPALITY | 25025000 | 0 |
| Vestfjord Enterprise Agency | 43000000 | 0 |
| Northbridge Materials ApS | 22237500 | 0 |
| Morrow Resource Recovery ApS | 20956250 | 0 |
| RenewLoop Denmark | 15837500 | 0 |
| LAKELAND REGIONAL COUNCIL | 14935000 | 0 |
| TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY | 30325000 | 0 |
| GREEN PATHWAYS OY | 43187500 | 0 |
| LAKELAND RESOURCE SERVICES OY | 33530000 | 0 |
| MineralCarbon Solutions Oy | 37975000 | 0 |
| TerraForm Innovations Oy | 38456250 | 0 |
| BALTIC INSTITUTE OF TECHNOLOGY | 36650000 | 0 |
| City of Valmont | 22406250 | 0 |
| EUROPEAN INSTITUTE OF MATERIALS | 21562500 | 0 |
| AEGEAN REGIONAL INNOVATION FUND | 13587500 | 0 |
| MUNICIPALITY OF PORTO VERDE | 22206250 | 0 |
| UNIVERSITY OF HARZ TECHNOLOGY | 57150000 | 0 |
| SAIMAA UNIVERSITY OF APPLIED SCIENCES | 34302500 | 0 |
| CycleReturn ApS | 0 | 0 |
| AFL | 0 | 1 |

| Extracted partner | Amount (cents) | Class | Unsure case | Amount outcome | Reason |
|---|---|---|---|---|---|
| NCS | 66670000 | supported_extra |  |  | name appears in the Docling Markdown |
| VEST | 25025000 | supported_extra |  |  | name appears in the Docling Markdown |
| LRC | 14935000 | supported_extra |  |  | name appears in the Docling Markdown |
| LBDA | 30325000 | supported_extra |  |  | name appears in the Docling Markdown |
| LRS | 33530000 | supported_extra |  |  | name appears in the Docling Markdown |
| MCS | 37975000 | supported_extra |  |  | name appears in the Docling Markdown |
| TFI | 38456250 | supported_extra |  |  | name appears in the Docling Markdown |
| BIT | 36650000 | supported_extra |  |  | name appears in the Docling Markdown |
| PV | 22206250 | supported_extra |  |  | name appears in the Docling Markdown |
| UHT | 57150000 | supported_extra |  |  | name appears in the Docling Markdown |
| SUAS | 34302500 | supported_extra |  |  | name appears in the Docling Markdown |
| CRTN | 0 | supported_extra |  |  | name appears in the Docling Markdown |
| AFL | 0 | matched |  | correct | same name |

<details><summary>Final record and gold set (JSON)</summary>

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban PVerials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NCS",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VEST",
      "requested_cents": 25025000
    },
    {
      "partner_name": "LRC",
      "requested_cents": 14935000
    },
    {
      "partner_name": "LBDA",
      "requested_cents": 30325000
    },
    {
      "partner_name": "LRS",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MCS",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TFI",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BIT",
      "requested_cents": 36650000
    },
    {
      "partner_name": "PV",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UHT",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SUAS",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CRTN",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": "2026-10-31T12:55:49Z",
    "source_file": "CIRCUNOVA.pdf"
  }
}
```

```json
{
  "proposal": {
    "proposal_acronym": "CIRCUNOVA",
    "proposal_title": "Circular Industry Networks for Regenerative Urban Materials",
    "call_identifier": "HORIZON-CL6-2026-01-two-stage",
    "submission_date": null
  },
  "proposal_facts": {
    "requested_total_cents": 600000000,
    "trl_start": null,
    "trl_target": null,
    "mcrl_start": null,
    "mcrl_target": null
  },
  "partners": [
    {
      "partner_name": "NORDIC CIRCULAR SYSTEMS OY",
      "requested_cents": 66670000
    },
    {
      "partner_name": "VESTFJORD MUNICIPALITY",
      "requested_cents": 25025000
    },
    {
      "partner_name": "Vestfjord Enterprise Agency",
      "requested_cents": 43000000
    },
    {
      "partner_name": "Northbridge Materials ApS",
      "requested_cents": 22237500
    },
    {
      "partner_name": "Morrow Resource Recovery ApS",
      "requested_cents": 20956250
    },
    {
      "partner_name": "RenewLoop Denmark",
      "requested_cents": 15837500
    },
    {
      "partner_name": "LAKELAND REGIONAL COUNCIL",
      "requested_cents": 14935000
    },
    {
      "partner_name": "TAMPEREEN KAUPUNKISEUDUN ELINKEINOJA KEHITYSYHTIO BUSINESS TAMPERE OY",
      "requested_cents": 30325000
    },
    {
      "partner_name": "GREEN PATHWAYS OY",
      "requested_cents": 43187500
    },
    {
      "partner_name": "LAKELAND RESOURCE SERVICES OY",
      "requested_cents": 33530000
    },
    {
      "partner_name": "MineralCarbon Solutions Oy",
      "requested_cents": 37975000
    },
    {
      "partner_name": "TerraForm Innovations Oy",
      "requested_cents": 38456250
    },
    {
      "partner_name": "BALTIC INSTITUTE OF TECHNOLOGY",
      "requested_cents": 36650000
    },
    {
      "partner_name": "City of Valmont",
      "requested_cents": 22406250
    },
    {
      "partner_name": "EUROPEAN INSTITUTE OF MATERIALS",
      "requested_cents": 21562500
    },
    {
      "partner_name": "AEGEAN REGIONAL INNOVATION FUND",
      "requested_cents": 13587500
    },
    {
      "partner_name": "MUNICIPALITY OF PORTO VERDE",
      "requested_cents": 22206250
    },
    {
      "partner_name": "UNIVERSITY OF HARZ TECHNOLOGY",
      "requested_cents": 57150000
    },
    {
      "partner_name": "SAIMAA UNIVERSITY OF APPLIED SCIENCES",
      "requested_cents": 34302500
    },
    {
      "partner_name": "CycleReturn ApS",
      "requested_cents": 0
    },
    {
      "partner_name": "AFL",
      "requested_cents": 0
    }
  ],
  "metadata": {
    "extraction_timestamp": null,
    "source_file": "CIRCUNOVA_synthetic.pdf"
  }
}
```

</details>

