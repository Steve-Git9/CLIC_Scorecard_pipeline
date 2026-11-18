## AI Disclaimer

## Documentation of the use of AI-supported tools

The following AI-supported tools were used for the following purposes.

| AI-supported tool   | Type of support                  | Contribution                           |
|---------------------|----------------------------------|----------------------------------------|
| Chat GPT 5.2        | Idea generation                  | Initial brainstorming session          |
| Chat GPT 5.2        | Language analysis and correction | Rephrasing and elaboration of concepts |
| Mistral AI          | Language analysis and correction | Rephrasing and elaboration of concepts |
| Manus AI            | Idea generation                  | KPI enrichment                         |
| Grok                | Literature review                | Referencing help                       |

I hereby declare that when AI has been used not only as a tool but also as a source, APA citation guidelines have been applied. All content generated using AI tools and included in the thesis, whether as direct or indirect citations, is clearly identified in accordance with APA citation style.

## Abstract

Bygg Map is an innovative, data-driven platform designed to assess and map building energy efficiency across European cities at unprecedented scale and resolution. The project introduces a novel methodology that combines open Earth Observation data from the Copernicus Programme, advanced geospatial analysis, and machine learning to infer building energy performance through the analysis of thermal behaviour, urban morphology, surface materials, and environmental context. By moving beyond traditional, building-bybuilding energy audits, Bygg Map enables continuous, city-wide monitoring of energy efficiency using standardized, repeatable, and objective indicators. The core innovation of Bygg Map lies in its ability to translate heterogeneous satellite imagery and spatial data into structured, high-quality datasets and to apply climate-aware machine learning models capable of classifying buildings according to their energy efficiency. This approach ensures comparability across diverse European climates and urban forms, while maintaining high scientific rigor and scalability. Results are delivered through a cloud-based Software-as-a-Service platform featuring an intuitive, map-based interface that supports evidence-based decision-making. Bygg Map is primarily targeted at municipalities and public authorities, providing them with a powerful tool to identify critical buildings and districts, prioritize renovation investments, and design transparent, fair, and data-oriented energy policies. Starting from a pilot implementation in Sofia, Bulgaria, the project aims to scale across Europe and establish a shared reference infrastructure for urban energy intelligence. Bygg Map represents a

## Bygg Map

technological and methodological breakthrough in the transition toward sustainable, resilient, and climateneutral cities.

## 1. Excellence

Financial constraints are among the main barriers to improving building stocks; therefore, identifying the most energy-inefficient and vulnerable areas are essential to prioritize critical buildings and maximize renovation benefits. Bygg Map builds on well-established Earth Observation research and long-running satellite missions such as Landsat and Copernicus Sentinel, whose thermal and multispectral data have been validated for urban analysis, including heat dispersion, urban heat island effects, and material-related thermal behaviour[1], [2], [3]. These mature datasets provide a reliable foundation for scalable, AI-driven energy efficiency classification.

Bygg Map does not rely on a specific, single and similar project from the Cordis platform. For this reason is not possible to define an undisputable starting point in regards to the Technology Readiness Level according to Cordis Taxonomy. We assume that the TRL4 can be a suitable label and the milestones that have led to these technological components justify our assumption. The development of Bygg Map is enabled by a sequence of key scientific and technological milestones that progressively transformed Earth Observation data into operational urban intelligence. The first milestone is the consolidation of Earth Observation origins, marked by the long-term availability of Landsat data and, more recently, the Copernicus Sentinel missions, which established continuous, high-quality, and open-access monitoring of land surface temperature, land cover, and urban morphology. A second milestone is the maturation of classification models in geospatial and environmental sciences, where machine learning techniques such as Random Forest and ensemble methods proved effective in linking remotely sensed indicators to urban and building-level characteristics. A third milestone is the advent of deep vision techniques, which enabled automated interpretation of large volumes of satellite imagery through convolutional neural networks, dramatically increasing scalability and reducing manual processing. Additional crucial milestones include the rise of cloud computing for large-scale geospatial processing, the standardization of European spatial datasets through Copernicus services, and the increasing policy demand for data-driven tools to support municipal energy and climate strategies. All these milestones, now at a consolidated level of development, make possible the launch of Bygg Map project.

This project aims then to basically work on a TRL5 for the whole timespan with prototyping and testing in real case scenario to then, in the last quarter of the third year, having a market ready solution with TRL6.

## 1.1 Technological Breakthrough

Bygg Map represents a technological breakthrough in the measurement, analysis, and governance of urban energy efficiency at continental scale. It introduces a new paradigm in which satellite Earth Observation, geospatial intelligence, and artificial intelligence are integrated into a single operational system capable of transforming raw environmental data into actionable policy intelligence. Unlike traditional approaches based on isolated energy audits, self-reported data, or limited statistical samples, Bygg Map enables automated, repeatable, and scalable analysis of the entire building stock, leveraging open European satellite data and progressively integrating additional data sources.

The foundation of the platform is built on open-access Earth Observation data from the Copernicus Programme, particularly multispectral and thermal imagery from Sentinel missions, which provide consistent, pan-European coverage and standardized quality. These data have been extensively validated for urban thermal and land-cover analysis in scientific literature[1]. By relying on this public infrastructure, Bygg Map ensures transparency, technological sovereignty, long-term sustainability, and compatibility with European digital strategies, while remaining extensible to higher-resolution commercial datasets where required.

Recognizing that satellite imagery alone cannot capture the full complexity of urban energy behaviour, Bygg Map introduces an advanced multi-source data fusion architecture. Copernicus data are integrated with GIS datasets, Digital Surface Models, land-use and land-cover maps, and climate and meteorological data. These heterogeneous datasets, characterized by different formats, resolutions, and temporal frequencies, are harmonized through automated pipelines that perform georeferencing, resampling, normalization, and temporal alignment. This process enables the creation of a consistent, city-scale digital representation of the built environment from an energy perspective, a capability increasingly recognized as critical for urban analytics [4].

A key innovation of Bygg Map is the use of computer vision techniques to interpret satellite imagery automatically. Convolutional neural networks process thermal and multispectral data to detect heat dispersion patterns, surface temperature gradients, material-related behaviours, and microclimatic effects. These visual patterns are converted into structured numerical features, enabling large-scale machine learning analysis. Image-derived features are then combined with contextual variables, such as building geometry, urban morphology, and climate classifications. Deep learning supports image interpretation, while classical machine learning models (e.g., Random Forest and ensemble methods) perform robust and interpretable energy efficiency classification [5].

To ensure climatic relevance, Europe is divided into macro-climatic zones, and models are adapted accordingly. This climate-aware architecture avoids one-size-fits-all assumptions and embeds environmental context directly into the analytical logic, a recognized best practice in urban energy modelling [6]. The system operates on a monthly update cycle aligned with satellite revisit times, transforming Bygg Map into a continuously evolving platform rather than a static assessment tool.

The final output is a simple, standardized energy efficiency classification for each building, delivered through a cloud-based SaaS platform with an interactive map interface. This integration of advanced analytics with intuitive visualization enables municipalities to identify critical areas, prioritize investments, and justify decisions transparently. In summary, Bygg Map does not introduce a single isolated innovation, but rather integrates mature, validated technologies into a coherent operational system that replaces fragmented assessments with continuous, data-driven urban energy intelligence.

## 1.2 Objectives

A first fundamental objective is methodological: to develop and validate a data-driven approach that can reliably infer building energy efficiency from indirect physical indicators, such as heat dispersion, surface temperature patterns, urban morphology, and environmental context. We are going to numerically measure this objective using the Model Prediction Accuracy. With this KPI we are able to understand how accurate this data-driven approach predicts the actual building energy efficiency, comparing the prediction with ground truth data. These ground truth data will be extracted from the previous evaluations and labelling already in place in many European countries alongside with on-site evaluations that will be conducted specifically for this project's purpose. This KPI directly validates that the integrated satellite and GIS data reliably infer energy efficiency.

Target: ≥ 85% accuracy (meaning the model correctly predicts building energy efficiency classification in at least 85% of cases when compared to verified ground truth measurements).

A second objective is technological: to design a cloud-based platform that can process large volumes of geospatial and satellite data and transform them into intelligible outputs for non-technical users. In doing so, the project seeks to bridge the gap between advanced research and everyday administrative practice. This objective will be careful monitored with direct feedback and surveys and numerically through a Platform Usability Score. This KPI measures how easily non-technical users (municipal staff, decision-makers) can navigate and use the Bygg Map platform to access energy efficiency data and insights.

Target: ≥ 4 out of 5 (based on user satisfaction and usability testing with municipal staff).

A third objective is strategic: to support public decision-makers in assessing renovation and construction priorities. Instead of relying on fragmented surveys or political intuition, local governments will be able to base their renovation strategies on transparent, data-driven evidence. We are going to numerically measure this objective using the Building Stock Coverage Index. This KPI measures the platform's capability to monitor and assess a significantly larger number of buildings compared to traditional survey-based approaches. It tracks the ratio of buildings assessed through Bygg Map versus buildings previously covered by conventional energy audits or surveys.

Target: ≥ 95% building stock coverage (meaning Bygg Map can monitor and provide energy efficiency assessments for at least 95% of all buildings in a municipality).

A fourth objective is social and environmental: to contribute to the creation of more inclusive and sustainable cities. By identifying energy-inefficient buildings, Bygg Map indirectly highlights areas where residents are more exposed to energy poverty, thermal discomfort, and excessive energy costs. The platform therefore aims to support policies that not only reduce emissions, but also improve living conditions, reduce inequality, and enhance urban resilience in the face of climate change. We are going to numerically measure this objective using the Building Assessment Scale Multiplication Factor. This KPI will be calculated as ratio between buildings Assessed with Bygg Map divided by Buildings Assessed with Traditional Methods. For the calculation, obviously, similar timeframe and comparable resources will be taken into account.

Target: Ratio ≥ 10 (Bygg Map must assess at least 10 times more buildings than traditional methods within the same time period).

Finally, a long-term objective of Bygg Map is to establish a permanent, evolving infrastructure for urban energy intelligence. Starting from the pilot implementation in Sofia, Bulgaria, the project aims to expand progressively to other European cities, creating a living atlas of building energy performance. Over time, this atlas will become a strategic asset for Europe's energy transition, supporting climate targets, renovation strategies, and sustainable urban development.

## 1.3 Methodology

Bygg Map is based on an integrated, multi-layered analytical framework that combines Earth Observation, geospatial analysis, machine learning, and urban science to transform raw spatial data into actionable indicators of building energy efficiency. The methodology is designed to be scientifically robust, scalable across Europe, and adaptable to diverse climatic and urban contexts.

The first stage focuses on data acquisition, using open-access satellite imagery from the Copernicus Programme, particularly multispectral and thermal data from Sentinel missions. These are complemented by GIS datasets, building footprints, Digital Surface Models, land-use and climate data, and, where available, hyperlocal information from sensors and surveys. In this context, collaboration with the European project Collectif enables the integration of citizen-driven, hyperlocal environmental data.

The second stage involves automated data preprocessing and harmonization. Given the heterogeneity of the datasets, pipelines perform georeferencing, reprojection, resampling, cloud masking, noise reduction, temporal alignment, and normalization. Raster and vector data are integrated into a unified geospatial database, with quality control procedures ensuring data consistency and reliability.

The third stage addresses feature extraction. Computer vision techniques and convolutional neural networks are applied to satellite imagery to derive quantitative indicators related to heat dispersion, surface temperature gradients, building geometry, urban density, and shading effects. These indicators capture the thermal behaviour of buildings and their surrounding environment.

In the fourth stage, machine learning models are developed using a climate-aware approach. Europe is divided into macro-climatic zones, and models are adapted accordingly. Deep learning supports image interpretation, while classical machine learning algorithms combine extracted features with contextual data to classify buildings into energy efficiency categories.

The final stages focus on validation, deployment, and updating. Model outputs are calibrated against available reference data, such as energy certificates or surveys, and integrated into a cloud-based, map-driven platform.

Monthly data ingestion and model retraining ensure that results remain accurate, consistent, and up to date for decision-makers.

Figure 1 - Methodology (Created with ChatGPT 5.1)

<!-- image -->

## 2. Impact

## 2.1 Credibility of the impacts

Bygg Map will enter the market as a public-interest oriented technology platform designed to support evidence based urban energy policy. The primary target customers are municipalities, which face increasing pressure to meet climate targets, reduce emissions, and manage renovation budgets transparently. In addition, several other actors can benefit from the platform, including regional and national public authorities, energy agencies, utilities, energy service companies, development banks, real estate operators, and climate-focused consultancies. These stakeholders share a common need for reliable, large-scale information on building energy performance.

Bygg Map's pilot implementation in Sofia's municipality in Bulgaria, will serve as a real-world testbed for validating this technological framework. Sofia represents a complex urban environment with diverse building typologies, climate conditions, and socio-economic patterns. Deploying the system in such a context will allow the platform to test its scalability, robustness, and adaptability.

## 2.1.1 Support of the commercialization and product features

The planned activities directly shape both the business model and the core product features of Bygg Map. The pilot in Sofia will be used to co-design the platform with municipal stakeholders, ensuring that the map interface, scoring system, and analytical outputs match real operational needs in public administration. Iterative development cycles will translate user feedback into concrete features such as multi-scale visualization (city, district, building), exportable reports for policy planning, and prioritization layers for renovation strategies. Through this the product development can be aligned with market expectations. Some additional features may include a clear identification of on-going restructuring or renovation and also a 'suggestions' tab with potential spaces within cities can construct more in or add mire vegetation, obtained with data driven analysis.

Figure 2 - Bygg Map Dashboard Snapshot

<!-- image -->

From a business perspective, the planned activities validate Bygg Map's Software-as-a-Service (SaaS) model designed to public authorities and urban planners. The product evolves from a research prototype (TRL5) into a market-ready platform offering premium analytics modules, and integration services for existing municipal GIS systems (TRL6).

## 2.1.2 Strategy for management of intellectual property

The intellectual property strategy focuses on protecting Bygg Map's unique combination of data fusion pipelines, modelling architecture, and AI-driven energy classification methods. Even if the foundational layer of data will be originated by open-source EO data, the orchestration logic, model configurations, and operational workflows constitute proprietary know-how. This balanced approach preserves interoperability exalting the power of open-source data for a common purpose, while safeguarding competitive advantage. During the whole process through documentation of data analysis and development of the product will be conducted in order to safeguard the integrity of the project and establish ownership and accountability for the project. Clear contracts will be established with the pilot municipality and other actors in order to clearly outline intellectual property ownership and usage rights.

## 2.1.3 Early market exploration and competitive landscape

Early market exploration targets medium-sized European municipalities lacking in-house analytical capacity. Structured interviews and the Sofia pilot partnership will test municipalities' willingness to pay, possible procurement models, and the perceived value. The potential competitors for Bygg Map can be identified as traditional energy auditing firms, smart-city dashboard providers, and remote-sensing analytics firms. Bygg Map differentiates itself by combining continental-scale coverage, building-level granularity, GDPR-safe design, and direct policy relevance. This urban-clustering based approach holds immense potential in terms of offering solutions to the data acquisition, and machine learning and AI technique integration challenges that municipalities face in their energy usage mapping [7].

The Sofia pilot functions as a living market test, validating demand and positioning. Continuing from the pilot and the data gathered from it a more targeted marketing strategy can be executed focusing on maximizing the benefits of the product and identifying the best suited municipalities. While remote sensing analytics research demonstrates the technical potential to infer building energy characteristics from aerial imagery, street view, and satellite data, these proof-of-concept studies remain largely academic or custom-made analyses rather than mature, operational products adopted by public authorities [8]. Bygg Map bridges this gap by operationalizing Earth observation and AI into a repeatable, cloud-native service that produces standardized, building-level energy intelligence across entire cities, rather than serving as a general dashboard or isolated research prototype. This positions Bygg Map in a distinct category that current dashboard platforms and remote sensing analytics offerings do not fully address.

## 2.1.3 Validation of problem

Bygg Map will validate the problem/solution fit by executing a structured and real-world focused approach that is based on two mechanisms. First an empirical validation will be conducted comparing AI outputs with existing energy certificates and renovation data. This will demonstrate the product's ability to produce robust solutions. Secondly a decision impact tracking system will be implemented that will measure whether the insights provided by Bygg Map actually influence actual renovation priorities. This will again provide realworld evidence of the validity of the product. These mechanisms help ensure that the product does not merely generate data but that it also helps to solve concrete problems.

## 2.1.4 Dissemination and exploitation plan

In its initial phase, the dissemination and exploitation plan of Bygg Map focuses on systematically engaging the actors who are responsible for urban energy planning and renovation decisions. Rather than relying on broad promotional activities, the project prioritises direct interaction with municipalities and public authorities whose operational needs align with the platform's capabilities. The pilot in Sofia provides a concrete reference case, demonstrating how the system can be embedded in real municipal workflows. The lessons and results from this deployment will be used in targeted workshops and technical sessions with other cities that match the intended user profile of Bygg Map. Snapshots and images of the first prototype will also be shared and posted before the final release in order to create positive attention. In parallel, participation in specialised conferences on urban analytics, energy systems, and geospatial innovation serves as a channel for peer-to-peer exchange, allowing the project to reach practitioners facing similar challenges and to identify additional municipalities interested in testing and adopting the approach. These activities are designed to establish a pipeline of 5-10 follower municipalities that can be approached for post-project deployment and replication.

A targeted awareness campaign will be conducted with CEE Bankwatch specifically focusing on Eastern Europe. This will be done through events and conferences, and visiting municipalities. CEE Bankwatch has specific knowledge about Eastern Europe and can act as the necessary bridge between local communities, grassroots organizations and municipalities. This ensures that the project does not remain limited to highcapacity cities, but creates pathways for uptake in regions where renovation needs are greatest and institutional capacity is lowest.

## 2.1.5 Scale up potential

Bygg Map's scalability comes from the standardized satellite data and cloud-native pipelines. The platform can be deployed in new cities with minimal marginal cost and very limited additional investment. Once building footprints and basic GIS layers are available, new urban areas can be onboarded rapidly, largely through automated processes. This means that with comparatively small incremental funding, the system can be expanded to hundreds of cities, making scale-up exceptionally efficient. This enables the creation of a continental market for urban energy intelligence, positioning Bygg Map as a de facto European reference system and opening pathways to global expansion in regions adopting similar satellite infrastructures.

## 2.1.6 Positive impact on the European Union

The impact of Bygg Map to enhance and support the goals of the Commission as formulated in the Renovation Wave initiative is significant and complementary. Using Sofia municipality as the location of the pilot project underlines the social aspects of identifying vulnerable areas of energy poverty. Targeting and prioritizing the order of the renovations by using Bygg Map brings efficiency and aid to meet the renovation goals. The most positive aspect for the EU is that Bygg Map essentially transforms fragmented local data into a shared European asset and that will support the EU in reaching climate and renovation targets, and support sustainable urban development.

## 2.2 Investment readiness

The project is structured to move Bygg Map from a research prototype to an investment-ready venture by systematically reducing technical, market, and execution risks. On the technical side, the Sofia pilot will deliver a fully operational Minimum Viable Product (MVP) demonstrating the complete value chain of the product, including satellite data ingestion, AI-based classification, cloud deployment, and a municipality facing interface. Clear performance KPIs (model accuracy, update frequency, onboarding time for new cities, system uptime) will be defined and tracked, creating objective proof of scalability and robustness.

On the market side, structured engagement with at least 5-10 municipalities will validate demand, procurement pathways, and willingness to pay. These engagements will aim to secure letters of intent, pilot agreements, and early-adopter commitments, providing concrete commercial traction.

On the organizational side, the project will define the venture structure, core roles (CTO, product, sales), and operational cost base. A detailed financial model will be developed, including customer acquisition costs, onboarding costs per city, expected annual recurring revenue, and infrastructure expenses. Together, these elements form an investor-ready package consisting of a validated MVP, pilot results, market evidence, IP strategy, and financial projections.

## 2.2.1 Plans for commercialization

The core business model is Software-as-a-Service for public authorities. The platform is designed as a continuously updated analytical service rather than a one off study. In terms of possible monetization routes in the future, Bygg Map could introduce a tier-based subscription model, keeping in mind the differences between municipalities' population sizes, budgets, and capabilities. The model would offer predictable costs, low upfront investment, and long-term operational value. This design would cater to the realities of the public sector's financial sensitivities on establishing new tools.

## 2.2.2 Go-to-market strategy

Bygg Map will enter the market as a public-interest-oriented technology platform designed to support evidence-based urban energy policy. The primary target customers are municipalities, which face increasing pressure to meet climate targets, reduce emissions, and manage renovation budgets transparently. The initial market entry will focus on European municipalities, starting with the pilot city of Sofia, Bulgaria, and then expanding to other cities through European programs and urban networks.

A more detailed go-to-market strategy will be developed with CGI Suomi that will facilitate and help outline the business modelling and EU scaling strategy and other possible customers beneficiaries will be evaluated, such as energy agencies, utilities, energy service companies, development banks, real estate operators, and climate-focused consultancies. Distribution will follow a dual channel strategy. First, direct sales will target municipalities through dedicated outreach, conferences, and networks of local governments. Second, Bygg Map will be promoted through European programs, climate initiatives, and urban innovation calls, where municipalities are already seeking tools to support their sustainability strategies.

## 3. Quality and effectiveness of the implementation

## 3.1 Quality and motivation of the team

## Management Center Innsbruck - Austria

Management Center Innsbruck (MCI) is the leading partner of Bygg Map utilizing their expertise in project management, financial oversight, and stakeholder coordination to ensure seamless collaboration and resource efficiency. The extensive experience in developing and managing digital platforms makes MCI particularly suitable to lead the Software-as-a-Service development of Bygg Map (WP5). Its expertise in user-centered design, cloud-based systems, and digital service management ensures that complex analytical outputs can be transformed into a stable, secure, and intuitive platform.

## Technical University of Cluj-Napoca - Romania

The Technical University of Cluj-Napoca is a leading technical institution with strong expertise in geospatial technologies, remote sensing, and data engineering. Its background in Earth Observation and spatial data processing makes it particularly suitable for managing satellite data acquisition and surface data integration. The university has the scientific capacity to handle large volumes of heterogeneous data and to translate raw imagery and unstructured information into structured, coherent, and analysis-ready datasets. This role is central to the entire Bygg Map pipeline, and the institution's technical rigor ensures data reliability from the very first stages.

## Norwegian University of Science and Technology - Norway

The Norwegian University of Science and Technology (NTNU) is internationally recognized for excellence in artificial intelligence, data science, and engineering research. NTNU brings advanced expertise in algorithm design, model optimization, and scientific validation, ensuring that classification models are accurate, robust, and adaptable across different climatic zones. The University demonstrated also a solid experience in energy efficiency and thermal insulation through recent contributions in paper publications, making this partner even a stronger candidate to supports the integration of technical modelling with environmental and urban studies.

## National Institute for Research and Development in Construction, Urban Planning and Sustainable Spatial Development - Romania

The Urban-Incerc is specialized in applied research related to buildings, cities, and territorial systems. Its role in validating dataset coherence and integrating Bygg Map outputs with other data sources is well aligned with its mission. The institute has deep expertise in construction typologies, urban systems, and spatial planning, enabling it to assess whether analytical results are realistic, consistent, and usable in real-world planning contexts. This ensures that technical outputs remain aligned with practical urban and construction realities.

## Sofia Municipality - Bulgaria

Sofia Municipality is a large and complex urban administration facing significant challenges related to building energy efficiency and urban sustainability. As the pilot city, it provides a real-world testing environment for Bygg Map, offering diverse building typologies, climatic conditions, and socio-economic patterns. The municipality's direct involvement ensures that the platform is tested under realistic administrative conditions, with feedback from actual end users. This role is essential for validating usability, policy relevance, and operational impact before scaling to other European cities.

## CGI Suomi Oy - Finland

CGI Suomi Oy is part of a global IT and consulting group with strong experience in digital transformation, public-sector innovation, and large-scale technology deployment. CGI can translate technological results into viable business models, define pricing and subscription strategies, and design pathways for expansion across Europe. Its experience with public administrations and EU-level projects ensures that Bygg Map can move efficiently from research to market.

## CEE Bankwatch - Czech Republic

CEE Bankwatch is a well-known civil society organization active in monitoring public investments, sustainability, and social impacts across Central and Eastern Europe. Its strong communication networks and advocacy experience make it particularly suitable for dissemination and community engagement. Bankwatch can ensure that Bygg Map results are communicated in an accessible way, reaching municipalities, civil society, and citizens. Its focus on transparency and public accountability aligns well with the project's goal of promoting fair and data-driven urban energy policies.

## 3.2 KPIs and milestones

Key Performance Indicators (KPIs) and milestones are important tools in measuring the progress of Bygg Map. By setting clear and concrete goals each work package can focus on their objectives and deliver results. This structure reflects the ambition of Bygg Map to evolve from a research prototype (TRL4) into a scalable, investment-ready SaaS platform for urban energy intelligence (TRL6).

Key milestones structure and the pathway to impact:

- Month 1: Start of the EO Data Acquisition and Elaboration
- Month 16: Database finalized → Deliverables D2.1-5
- Month 20: Machine Learning Modelling and Development → Deliverables D4.1-4
- Month 21: Saas Implementation → Deliverables D5.1-3
- Month 24: Pilot Project Start in Sofia Municipality → Deliverables D6.1-3
- Month 30: Pilot evaluation and first commercial commitments
- Month 33: Investor-ready business and scale-up plan → Deliverables D7.1-3.

Figure 3 - Milestones

<!-- image -->

Together these KPIs and milestones ensure continuous monitoring of progress toward a system that is not only technically robust but also usable, adoptable, and commercially viable. The framework explicitly demonstrates that Bygg Map can reach market readiness within 24-26 months and that once the core platform is established each additional city can be onboarded with minimal incremental investment, thus creating a highly attractive scale-up profile for European and global markets.

## 3.3 Work Plan and resources

In this chapter the 8 work packages will be presented. The GANTT Chart with a detailed timeline, the planned budget as well as a list of KPIs and deliverables can be found in the appendix.

| Project Management   |             |     |
|----------------------|-------------|-----|
| WP-01                | Leader: MCI | PMs |

| Tasks      |                                                                                                                                                                                                                                                                  |   MCI |   TUCN |   NTNU |   U- I |   SM |   CGI |   CEE |   Sum |
|------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------|--------|--------|--------|------|-------|-------|-------|
| T-1.1      | Administrative Management                                                                                                                                                                                                                                        |     3 |      1 |        |        |      |       |     1 |     5 |
| 01/09/2026 | 31/08/2029 Regularly organize project meetings to ensure that all partners are aligned on the development of key technologies. Use collaboration platforms to share progress on photosynthesis regulation models and facilitate communication.                   |       |        |        |        |      |       |       |       |
| T-1.2      | Technical Mangement                                                                                                                                                                                                                                              |     3 |      2 |      1 |        |      |       |       |     6 |
| 01/11/2026 | 31/08/2029 Monitor progress against key project milestones and track the progress of the dy-namic online platform. Ensure that reports are always up to date, correct and accessible to the EU and partners.                                                     |       |        |        |        |      |       |       |       |
| T-1.3      | Financial Management                                                                                                                                                                                                                                             |     3 |      2 |        |        |      |       |       |     5 |
| 01/09/2026 | 31/08/2029 Ensure the proper allocation of funds for tasks like platform development, AI sim- ulations and pilot trials. Monitor expenses and handle financial reporting for the EU's requirements in cooperation with financial officers.                       |       |        |        |        |      |       |       |       |
| T-1.4      | Risk Management                                                                                                                                                                                                                                                  |     2 |        |        |        |      |       |       |     2 |
| 01/09/2026 | 31/08/2029 Identify risks related to technology development, environmental factors, and data privacy (especially for personal data) that could impact project success. Regularly update risk assessments and ensure compliance with data protection regulations. |       |        |        |        |      |       |       |       |
| T-1.5      | Stakeholders and Partners Engagement                                                                                                                                                                                                                             |     4 |      2 |        |        |      |       |     3 |     9 |
| 01/09/2026 | 31/08/2029 Organize meetings and workshops to engage with stakeholders of real-world agri-cultural settings. Use stakeholders' feedback to improve project development and dissemination strategy.                                                               |       |        |        |        |      |       |       |       |
|            | Sum                                                                                                                                                                                                                                                              |    15 |      7 |      1 |      0 |    0 |     0 |     4 |    27 |

| WP Objectives   | WP Objectives                                                            |
|-----------------|--------------------------------------------------------------------------|
| O1.1            | Maintain alignment across all project partners on technology development |
| O1.2            | Monitor project progress against milestones and deliverables             |
| O1.3            | Ensure proper fund allocation and EU financial compliance                |

| WP Deliverables   | WP Deliverables                                                            |
|-------------------|----------------------------------------------------------------------------|
| D1.1              | ≥ 6 coordination meetings per year with ≥ 80% partner attendance           |
| D1.2              | ≥ 95% on-time milestone completion with monthly progress reports submitted |
| D1.3              | ≥ 90% budget accuracy with quarterly financial reports submitted to EU     |

| O1.4   | Identify and mitigate project risks and ensure data compliance        |
|--------|-----------------------------------------------------------------------|
| O1.5   | Engage stakeholders and incorporate feedback into project development |

D1.4 ≥ 4 risk assessments per year with

100% GDPR compliance verification

D1.5 ≥ 2 stakeholder workshops per year

with ≥ 80% feedback integration rate Produce policy briefs, case studies, and practitioner oriented guidelines. Translate technical results into actionable insights for decision makers. Disseminate outputs through EU and municipal networks.

| EO Data Acquisition, Surface data acquisition and Data Preparation - WP-02   | EO Data Acquisition, Surface data acquisition and Data Preparation - Leader: TUCN                                                                                                                                                                                   | PMs           |               | U-           |     |
|------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|---------------|--------------|-----|
| Tasks                                                                        |                                                                                                                                                                                                                                                                     | MCI TUCN NTNU | MCI TUCN NTNU | I SM CGI CEE | Sum |
| T-2.1                                                                        | Data Acquiring 31/12/2027 Acquire and optical                                                                                                                                                                                                                       |               | 6             | 2            | 8   |
| 15/09/2026                                                                   | high-resolution thermal satellite imagery from Copernicus and Landsat missions. This includes data selection, download, and initial radiometric and geometric corrections to prepare for analysis.                                                                  |               |               |              |     |
| T-2.2                                                                        | Data Integration                                                                                                                                                                                                                                                    |               | 3             | 3            | 6   |
| 01/01/2027                                                                   | 31/12/2027 Gather geospatial data, including building footprints, land use maps, and digital elevation models. Integrate this data with EO imagery to create a comprehensive geospatial database for the pilot                                                      |               |               |              |     |
| T-2.3                                                                        | area. Data Transformation                                                                                                                                                                                                                                           | 1             | 6             | 2            | 9   |
| 01/05/2027                                                                   | 31/12/2027 Convert raster satellite images, semi-structured geospatial files, and non-uniform auxiliary data into coherent data models through automated preprocessing, georeferencing, resampling, normalization, and metadata                                     |               |               |              |     |
| T-2.4                                                                        | standardization. Feature extraction                                                                                                                                                                                                                                 | 1             | 5             | 2 2          | 10  |
| 01/01/2027                                                                   | 15/03/2028 Process the integrated dataset to extract key features for energy efficiency assessment. This includes calculating land surface temperature, vegetation indices, and building metrics. These features will be used to train the machine learning models. |               |               |              |     |
| T-2.5                                                                        | Data Lineage Definition                                                                                                                                                                                                                                             | 1             | 7             | 2 2          | 12  |
| 01/01/2027                                                                   | 15/03/2028                                                                                                                                                                                                                                                          |               |               |              |     |

| Design data schemas, feature tables, and spatial databases that enable consistent integration of imagery-derived variables with vector-based and tabular datasets, ensuring interoperability, traceability, and direct usability for machine learning and analytical pipelines.   |                  |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| Sum 3                                                                                                                                                                                                                                                                             | 27 4 11 0 0 0 45 |

| WP Objectives   | WP Objectives                                                       |
|-----------------|---------------------------------------------------------------------|
| O2.1            | Acquire complete high-resolution thermal and optical satellite data |
| O2.2            | Create unified geospatial database from multiple data sources       |
| O2.3            | Convert heterogeneous data into standardized analytical formats     |
| O2.4            | Generate machine learning-ready features from integrated datasets   |
| O2.5            | Establish schemas ensuring data traceability and interoperability   |

| WP Deliverables   | WP Deliverables                                                     |
|-------------------|---------------------------------------------------------------------|
| D2.1              | ≥ 95% geographic coverage                                           |
| D2.2              | Composite quality score ≥ 0.90.                                     |
| D2.3              | ≥ 98% of raw data successfully transformed and georeferenced        |
| D2.4              | ≥ 50 engineered features extracted and validated for model training |
| D2.5              | lineage documentation with 100% metadata coverage                   |

| Validate the coherency obtained dataset and integrate it with other data sources - WP-03 - Tasks   | Validate the coherency obtained dataset and integrate it with other data sources - Leader: U-I                                                                                                                                                                               |   PMs - MCI |   TUCN |   NTNU |   U- I SM | CGI   | CEE   |   Sum |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|--------|--------|-----------|-------|-------|-------|
| T-3.1                                                                                              | Accuracy validation                                                                                                                                                                                                                                                          |             |      3 |        |         6 |       |       |     9 |
| 01/11/2026                                                                                         | 31/12/2027 Conduct comprehensive quality assessment of satellite imagery and surface data. Validate spatial accuracy, temporal consistency, radiometric calibration, and data completeness. Identify and document data gaps, anomalies, and inconsistencies across datasets. |             |        |        |           |       |       |       |
| T-3.2                                                                                              | Data integration 1                                                                                                                                                                                                                                                           |             |      2 |        |         4 |       |       |     6 |
| 01/01/2027                                                                                         | 31/12/2027 Integrate satellite and surface datasets with building registry, cadastral records, and municipal property databases. Perform spatial matching, resolve conflicts between datasets, and create unified building identification system.                            |             |        |        |           |       |       |       |
| T-3.3 01/01/2027                                                                                   | Data Integration 2 31/12/2027                                                                                                                                                                                                                                                |           2 |        |      4 |           |       |       |     6 |

|            | Incorporate energy consumption data from utility companies, climate data from meteorological stations, and building performance certificates. Align temporal and spatial scales.                                                                            |                     |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|
| T-3.4      | Quality standard and metadata management                                                                                                                                                                                                                    | 1 3 4               |
| 01/01/2027 | 15/03/2028 Establish comprehensive metadata management system documenting all data sources, collection methods, quality standards, and update frequencies. Implement data governance policies, version control, and audit trails for data lineage tracking. |                     |
|            | Sum                                                                                                                                                                                                                                                         | 6 20 18 17 0 0 0 61 |

| WP Objectives   | WP Objectives                                                         |
|-----------------|-----------------------------------------------------------------------|
| O3.1            | Validate satellite and surface data quality and completeness          |
| O3.2            | Unify building identification across multiple administrative datasets |
| O3.3            | Harmonize energy consumption and climate data with building datasets  |
| O3.4            | Establish complete data governance and lineage tracking system        |

| WP Deliverables   | WP Deliverables                                                                                     |
|-------------------|-----------------------------------------------------------------------------------------------------|
| D3.1              | ≥ 95% data quality score across spatial accuracy, temporal consistency, and radiometric calibration |
| D3.2              | ≥ 98% of buildings successfully matched and integrated across ≥ 3 registries                        |
| D3.3              | ≥ 90% temporal and spatial alignment achieved across energy, climate, and building data             |
| D3.4              | 100% metadata documentation coverage with version control and audit trails implemented              |

<!-- image -->

| Machine Learning model development, testing and validation - WP-04 - Tasks   | Machine Learning model development, testing and validation - Leader: NTNU                                                                                                                                                        |   PMs - MCI |   TUCN |   NTNU | U- I SM   | CGI   | CEE   |   Sum |
|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|--------|--------|-----------|-------|-------|-------|
| T-4.1                                                                        | Database evaluation and Model Selection                                                                                                                                                                                          |           1 |      2 |      5 |           |       |       |     8 |
| 01/10/2027                                                                   | 01/01/2028 Evaluate and select appropriate machine learning algorithms for predicting building energy efficiency. Design model architectures, define hyperparameters, and establish baseline performance metrics for comparison. |             |        |        |           |       |       |       |
| T-4.2                                                                        | Model training or fine-tuning                                                                                                                                                                                                    |           1 |      1 |      7 |           |       |       |     9 |
| 01/01/2028                                                                   | 01/03/2028                                                                                                                                                                                                                       |             |        |        |           |       |       |       |

|            | Train or fine-tune the selected machine learning models using the prepared dataset from Sofia Municipality. Implement cross- validation, hyperparameter tuning, and regularization techniques to optimize model performance. Document training procedures and convergence analysis.   |                   |
|------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------|
| T-4.3      | Performances evaluation                                                                                                                                                                                                                                                               | 1 2 5 8           |
| 01/02/2028 | 01/04/2028 Validate trained models using independent test datasets and cross-validation techniques. Calculate performance metrics (accuracy, precision, recall, F1- score, AUC-ROC). Conduct error analysis and identify model limitations and failure modes.                         | 7                 |
| T-4.4      | Model testing, validation and traceability                                                                                                                                                                                                                                            | 1 2 4             |
| 01/04/2028 | 15/06/2028 Test model robustness against data variations, missing values, and geographic variations across different European cities. Develop comprehensive technical documentation for model deployment and create a reproducible model pipeline. Sum                                | 4 7 21 0 0 0 0 32 |

| WP Objectives   | WP Objectives                                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------------------------|
| O4.1            | Complete a comparative analysis of candidate machine learning algorithms with justification for the selection. |
| O4.2            | Finalize the model training with weights and parameters saved in production-ready format.                      |
| O4.3            | Conduct a comprehensive validation report with performance metrics on test and validation datasets.            |
| O4.4            | Test a reproducible model pipeline code with version control and deployment guidelines.                        |

| WP Deliverables   | WP Deliverables                                                                                       |
|-------------------|-------------------------------------------------------------------------------------------------------|
| D4.1              | ≥ 3 candidate algorithms evaluated with documented performance comparison and selection justification |
| D4.2              | ≥ 95% model convergence achieved with weights saved and validated for deployment                      |
| D4.3              | F1-Score ≥ 0.85 on test dataset with ≥ 90% accuracy on validation dataset                             |
| D4.4              | 100% code reproducibility with version control and deployment documentation completed                 |

| Saas Development - WP-05 - Tasks   | Saas Development - Leader: MCI         |   PMs - MCI | TUCN   |   NTNU | I SM   | CGI   | CEE   |   Sum |
|------------------------------------|----------------------------------------|-------------|--------|--------|--------|-------|-------|-------|
| T-5.1                              | Backend and Infrastructure Development |           3 |        |      2 |        |       |       |     5 |

| 01/03/2027       | 01/11/2027 Implement cloud-native architecture and data pipelines. Integrate EO ingestion, harmonized datasets (WP3), and ML outputs (WP4). Ensure security, uptime, and performance.                                 |              |
|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| T-5.2 01/07/2027 | Frontend and User Interface Design 3 01/05/2028 Design interactive map-based UI. Implement multi-scale navigation (from city to district and to building).                                                            | 1 4          |
| T-5.4 01/05/2028 | Conduct usability testing with Sofia Municipality. Improvements and adjustments 3 1 01/08/2029 Improve and adjust the dashboard following the feedback and requirements from consortium partners. Improve clarity and | 1 1 1 7      |
| T-5.5            | interpretability of analytics. Increase robustness and performance. Multi-City Readiness and Automation 2 3                                                                                                           | 5            |
|                  | 01/08/2029 Develop automated onboarding workflow for new cities. Implement configuration for climate zones and datasets. Create deployment guidelines for new municipalities.                                         |              |
| 01/05/2028       | Sum 11 4                                                                                                                                                                                                              | 3 1 1 0 1 21 |

| WP Objectives   | WP Objectives                                                                                    |
|-----------------|--------------------------------------------------------------------------------------------------|
| O5.1            | Transform the analytical pipeline developed in WP2-WP4 into a stable, cloud-based SaaS platform. |
| O5.2            | Deliver an intuitive, non-technical user interface for municipalities and decision- makers.      |
| O5.3            | Ensure that the platform is operationally scalable and ready for multi-city deployment.          |
| O5.4            | Enable secure, reliable, and compliant operation in public-sector IT environments.               |

| WP Deliverables   | WP Deliverables                                                               |
|-------------------|-------------------------------------------------------------------------------|
| D5.1              | ≥ 99.5% platform uptime with ≤ 2 second average response time                 |
| D5.2              | Usability score ≥ 4.0 out of 5.0 from municipal staff testing                 |
| D5.3              | Platform processes ≥ 10 cities simultaneously without performance degradation |
| D5.4              | 100% GDPR compliance                                                          |

| Pilot Demonstrations in Eastern Europe - WP-06 - Tasks   | Pilot Demonstrations in Eastern Europe - Leader: SM   |   PMs - MCI | TUCN   | NTNU   |   U- I SM | CGI   |   CEE |   Sum |
|----------------------------------------------------------|-------------------------------------------------------|-------------|--------|--------|-----------|-------|-------|-------|
| T-6.1                                                    | Pilot Preparation and Training                        |           2 |        |        |         7 |       |     2 |    11 |
| 01/07/2028                                               | 31/12/2028                                            |             |        |        |           |       |       |       |

|                  | Configure and deploy a dedicated Bygg Map instance for Sofia. Train municipal staff on platform use and interpretation of outputs.                                                                                 |              |    |    |        |    |    |
|------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------|----|----|--------|----|----|
| T-6.2 01/09/2028 | Operational Use and Monitoring 01/03/2029 Deploy the platform in live urban planning and renovation Monitor system usage, performance,                                                                             | 2 workflows. |    |    | 7      |  1 | 10 |
| T-6.3            | and adoption by municipal users. Collect quantitative metrics and qualitative feeback from end users. Evaluation and Refinement                                                                                    | 3            |    |    | 4      |    |  7 |
| 01/01/2029       | 01/06/2029 Evaluate analytical accuracy, usability, and decision-making impact. Assess organisational adoption and operational value. Translate findings into structured improvement requirements for WP4 and WP5. |              |    |    |        |    |    |
|                  |                                                                                                                                                                                                                    | Sum 7        |  0 |  0 | 0 18 0 |  3 | 28 |

| WP Objectives   | WP Objectives                                                                            |
|-----------------|------------------------------------------------------------------------------------------|
| O6.1            | Validate Bygg Map in a real municipal context.                                           |
| O6.2            | Demonstrate operational value for urban planning and renovation strategy.                |
| O6.3            | Provide empirical feedback to refine WP4- WP5 outputs.                                   |
| O6.4            | Generate evidence and reference material to support replication in other municipalities. |

| WP Deliverables   | WP Deliverables                                                                        |
|-------------------|----------------------------------------------------------------------------------------|
| D6.1              | ≥ 95% of platform features tested and validated with pilot municipality                |
| D6.2              | ≥ 80% of municipal planners report increased decision-making confidence using platform |
| D6.3              | ≥ 50 improvement recommendations documented and ≥ 70% implemented in refinements       |
| D6.4              | Complete replication guide with ≥ 5 case studies and lessons learned documented        |

| Exploitation, Business Modelling & EU Scaling Strategy - WP-07   | Exploitation, Business Modelling & EU Scaling Strategy - Leader: CGI                                                                                                                                                                                       | PMs   |      |      |      |    |     |     |     |
|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------|------|------|------|----|-----|-----|-----|
| Tasks                                                            |                                                                                                                                                                                                                                                            | MCI   | TUCN | NTNU | U- I | SM | CGI | CEE | Sum |
| T-7.1                                                            | Market Segmentation & Value Proposition                                                                                                                                                                                                                    | 2     |      |      |      |    | 4   |     | 6   |
| 01/08/2027                                                       | 01/02/2028 Identify target customer segments across municipalities, energy agencies, and public housing providers. Analyze user needs and procurement constraints. Position Bygg Map relative to audits, smart-city dashboards, and EO analytics services. |       |      |      |      |    |     |     |     |
| T-7.2                                                            | Business Model & Pricing                                                                                                                                                                                                                                   | 2     |      |      |      |    | 4   |     | 6   |
| 01/02/2028                                                       | 01/12/2028                                                                                                                                                                                                                                                 |       |      |      |      |    |     |     |     |

|            | licensing models for public authorities. Define tiered pricing aligned with municipality size and building stock. Test pricing assumptions and willingness to   | Design SaaS-based subscription and pay with sample municipalities.   |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |   Design SaaS-based subscription and pay with sample municipalities. |
|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|
| T-7.3      | EU Scaling & Investment Readiness                                                                                                                               | 2                                                                    |                                                                      |                                                                      |                                                                      |                                                                      |                                                                    4 |                                                                      |                                                                    6 |
| 01/12/2028 | 01/09/2029 Define a structured EU replication playbook. Seek commitments and from follower cities. Prepare facing material and                                  |                                                                      |                                                                      |                                                                      |                                                                      |                                                                      |                                                                      |                                                                      |                                                                      |
|            | rollout and early expressions of interest investor post-project commercialization roadmap.                                                                      | Sum 6                                                                |                                                                    0 |                                                                    0 |                                                                    0 |                                                                    0 |                                                                   12 |                                                                    0 |                                                                   18 |

| WP Objectives   | WP Objectives                                                                                |
|-----------------|----------------------------------------------------------------------------------------------|
| O7.1            | Define a sustainable business model for Bygg Map.                                            |
| O7.2            | Design a pan-European scaling strategy.                                                      |
| O7.3            | Strengthen market and investment preparedness through validated pricing and reference cases. |

| WP Deliverables   | WP Deliverables                                                                                          |
|-------------------|----------------------------------------------------------------------------------------------------------|
| D7.1              | Realize a business model document with ≥ 3 revenue scenarios and financial projections for 5 years       |
| D7.2              | Scaling strategy covering ≥ 10 European countries with implementation timeline and resource requirements |
| D7.3              | Validated pricing model with ≥ 3 reference cases and investment pitch deck completed                     |

| Dissemination, Communication & Community Engagement - WP-08 - Tasks   | Dissemination, Communication & Community Engagement - Leader: CEE                                                                                                                                           |   PMs - MCI | TUCN   | NTNU   |    | I SM   |   CGI |   CEE |   Sum |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------|--------|--------|----|--------|-------|-------|-------|
| T-8.1                                                                 | Communication Strategy & Branding                                                                                                                                                                           |           1 |        |        |    |        |       |     4 |     5 |
| 01/04/2027                                                            | 01/09/2029 Define project messaging, narrative, and visual identity. Select dissemination channels targeting municipalities and EU stakeholders. Ensure alignment with exploitation and scaling objectives. |             |        |        |    |        |       |       |       |
| T-8.2                                                                 | Targeted Outreach & Events                                                                                                                                                                                  |           1 |        |        |  1 |        |       |     3 |     5 |
| 01/10/2027                                                            | 01/09/2029 Present project results at specialized conferences and city networks. Organize pilot showcases and targeted workshops for municipalities. Engage follower cities through peer-to-peer exchange.  |             |        |        |    |        |       |       |       |
| T-8.3 01/09/2027                                                      | Policy & Practitioner Dissemination 01/09/2029                                                                                                                                                              |           1 |        |        |  1 |        |     1 |     3 |     6 |

<!-- image -->

| WP Objectives   | WP Objectives                                                              |
|-----------------|----------------------------------------------------------------------------|
| O8.1            | Ensure visibility among municipalities, policymakers, and EU stakeholders. |
| O8.2            | Build a community of follower cities.                                      |
| O8.3            | Support uptake beyond the pilot.                                           |
| O8.4            | Facilitate engagement between municipalities.                              |

| WP Deliverables   | WP Deliverables                                                                                |
|-------------------|------------------------------------------------------------------------------------------------|
| D8.1              | ≥ 10 publications, ≥ 5 conference presentations, and ≥ 5 Linkedin Post per year                |
| D8.2              | ≥ 5 municipalities engaged in community network with social media engagement                   |
| D8.3              | ≥ 3 additional municipalities interaxcted with Bygg Map with documented implementation success |
| D8.4              | ≥ 4 inter-municipal workshops organized with ≥ 100 municipal representatives participating     |

## 4. References

- [1] Voogt, J. A., &amp; Oke, T. R. (2003). Thermal remote sensing of urban climates. Remote Sensing of Environment, 86(3), 370-384. doi:10.1016/S0034-4257(03)00079-8
- [2] Weng, Q., Lu, D., &amp; Schubring, J. (2004). Estimation of land surface temperature-vegetation abundance relationship for urban heat island studies. Remote Sensing of Environment, 89(4), 467-483. doi:10.1016/j.rse.2003.11.005
- [3] Pesaresi, M., Melchiorri, M., Siragusa, A., Kemper, T. (2016). Atlas of the Human Planet. Mapping Human Presence on Earth. JRC Science For Policy Report, European Commission.
- [4] Wang, C., Ferrando, M., Causone, F., Jin, X., Zhou, X., &amp; Shi, X. (2022). Data acquisition for urban building energy modeling: A review. Building and Environment, 217, 109056.
- [5] Breiman, L. (10 2001). Random Forests. Machine Learning, 45, 5-32. doi:10.1023/A:1010950718922
- [6] Santamouris, M., Cartalis, C., Synnefa, A., &amp; Kolokotsa, D. (2015). On the impact of urban heat island and global warming on the power demand and electricity consumption of buildings-A review. Energy and Buildings, 98, 119-124. doi:10.1016/j.enbuild.2014.09.052
- [7] Jing, C., Du, M., Li, S., &amp; Liu, S. (2019). Geospatial dashboards for monitoring smart city performance. Sustainability, 11(20), 5648. https://doi.org/10.3390/su11205648
- [8] Mayer, K., Haas, L., Huang, T., Bernabé-Moreno, J., Rajagopal, R., &amp; Fischer, M. (2023). Estimating building energy efficiency from street view imagery, aerial imagery, and land surface temperature data. Applied Energy, 333, 120542. doi:10.1016/j.apenergy.2022.120542

## 5. Appendix

Figure 4 - Gannt Chart

<!-- image -->

Table 1 - Budget Allocation

| Partner   |   Total PM | %      | Requested grant €   |
|-----------|------------|--------|---------------------|
| MCI       |         55 | 23,63% | € 590,625.00        |
| TUCN      |         65 | 18,63% | € 465,625.00        |
| NTNU      |         47 | 29,95% | € 748,625.00        |
| U-I       |         29 | 8,18%  | € 204,375.00        |
| SM        |         21 | 5,78%  | € 144,375.00        |
| CGI       |         13 | 7,80%  | € 195,000.00        |
| CEE       |         18 | 6,06%  | € 151,375.00        |
| Tot       |            |        | € 2,500,000.00      |