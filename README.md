# Greater-Manchester-Tweet-Redistribution

A spatial data science project that applies a **weighted redistribution algorithm** to reduce false hotspots in ambiguously geocoded social media data.

This project uses tweet point data for Greater Manchester and redistributes each point within its administrative unit based on a **population-density weighting surface**, producing a more spatially plausible continuous activity surface than direct point mapping or naive heatmaps.

---

## Project Overview

Spatial point datasets are often affected by **location uncertainty**. In many real-world cases, events are only geocoded to a coarse administrative unit rather than their true location. If these points are mapped directly, the result can be misleading, creating **artificial clusters** that reflect the geometry of reporting units rather than actual activity patterns.

To address this problem, this project implements a **weighted redistribution approach** inspired by Huck et al. (2015). For each ambiguously located tweet:

1. Multiple candidate points are randomly generated within the relevant district
2. A population raster is used to identify the most plausible candidate location
3. The selected point is expanded into a distance-decay surface
4. All individual surfaces are accumulated into a final continuous output raster

The result is a more realistic representation of the spatial distribution of tweet activity across Greater Manchester.

> 
> ## Academic Context
> 
> This project is based on a university coursework assignment involving the implementation of the weighted redistribution algorithm from Huck et al. (2015).
> 
> While the underlying programming techniques were learned through weekly course practicals, the complete workflow, adaptation, analysis, visualisation, and project presentation were completed by the author.
> 

---

## Results

<h3>Weighted redistribution output</h3>
<img src="figure/n_candidates_20.png" alt="Weighted redistribution output with n_candidates = 20" width="650">

<h3>Naive heatmap</h3>
<img src="figure/naive_heatmap.png" alt="Naive heatmap" width="650">
Compared with direct mapping, the redistributed surface，the redistribution one reduces the appearance of artificial hotspots centred on administrative units, concentrates higher weighted values in denser urban areas, produces localised peaks rather than uniform district-centred blobs.

This makes the result more spatially plausible for exploratory analysis of social media activity.

## Study Area

**Greater Manchester, United Kingdom**

<h3>Population-weighted tweet map</h3>
<img src="figure/pop_tweets_map.png" alt="Population-weighted tweet map" width="650">

The analysis uses district boundaries, ambiguously geocoded tweet data, and a population density raster to model likely tweet activity patterns across the city-region.

## Methodology

### 1. Random candidate point generation

For each tweet associated with a district, multiple random candidate points are generated inside the district polygon.

### 2. Population-weighted candidate selection

Candidate points are sampled against a population raster, and the point with the highest raster value is selected as the most likely location.

### 3. Radius calculation

An influence radius is calculated based on administrative area and a scaling parameter.

### 4. Distance-decay redistribution

Each selected point is expanded using a circular kernel with linear distance decay.

### 5. Output surface generation

The weighted contributions of all redistributed points are accumulated into a final continuous surface representing probable tweet intensity.

## Key Features

- Handles **spatially ambiguous point data**
- Uses **population density** as a weighting surface
- Produces a **continuous redistribution surface**
- Includes basic robustness controls:
    - maximum attempts for random point generation
    - skipping NoData raster cells
- Visualises the result as a mapped output with:
    - district boundaries
    - colour bar
    - north arrow
    - scale bar


## Sensitivity to Parameters

This project explored how the number of candidate points (`n_candidates`) affects redistribution behaviour. **Lower values** (e.g. 10) produce more scattered hotspots. **Higher values** (e.g. 50) produce more stable and concentrated outputs. A mid-range setting was used as a practical balance between stability and computational.

This highlights that weighted redistribution is sensitive to parameter choice and should be interpreted carefully.


## Project Structure

```bash
weighted-redistribution/
│
├── **data/**
│   ├── wr/
│   │   ├── 100m_pop_2019.tif
│   │   ├── gm-districts.shp
│   │   └── level3-tweets-subset.shp
│
├── out/
│   └── tweets_heat_map.png
│
├── src/
│   └── weighted_redistribution.py
│
└── README.md
```

## technologies Used

**Python,**

**GeoPandas**

**NumPy**

**Pandas**

**Shapely**

**scikit-image**

**Matplotlib**


## Example Output

### Weighted redistribution output surface

<h3>Weighted redistribution output</h3>
<img src="figure/n_candidates_10.png" alt="Weighted redistribution candidates = 10" width="650">

<h3>Weighted redistribution output</h3>
<img src="figure/n_candidates_50.png" alt="Weighted redistribution candidates = 50" width="650">

### Parameter comparison
You may also include additional figures comparing different parameter values, for example:

- `n_candidates = 10`
- `n_candidates = 20`
- `n_candidates = 50`

These help demonstrate the sensitivity and robustness of the redistribution process.

## Limitations

The algorithm relies exclusively on population density as the weighting surface. However, tweet activity in urban environments is shaped by a range of additional factors, including land-use characteristics (for example, shopping centres, transport hubs, and parks), mobile network coverage, and demographic differences among users. The omission of these factors means that some patterns of social media activity may not be fully captured by the current weighting scheme.

Furthermore, the population dataset used in this study represents conditions in 2019. Subsequent changes in urban development and population distribution within Greater Manchester may introduce discrepancies between the weighting surface and present-day conditions, potentially affecting the accuracy of the redistribution results.

## References

Huck, J., Whyatt, D. and Coulton, P. (2015). *Visualizing patterns in spatially ambiguous point data*. Journal of Spatial Information Science, 10, 47–66.

van der Walt, S. et al. (2014). *scikit-image: image processing in Python*. PeerJ, 2, e453.

## Author
Ziyao Zhao

MSc GIS| The university of Manchester
