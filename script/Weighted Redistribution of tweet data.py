# -*- coding: utf-8 -*-
from time import perf_counter
# set start time
start_time = perf_counter()    

# --- NO CODE ABOVE HERE ---

from geopandas import read_file, gpd
from rasterio import open as rio_open
from rasterio.plot import show as rio_show
from rasterio.transform import rowcol
from matplotlib.pyplot import subplots, savefig
import numpy as np
from skimage.draw import disk   
import pandas as pd
from shapely.geometry import Point
import math
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib_scalebar.scalebar import ScaleBar
from skimage.filters import gaussian



#add data
# open the raster file
gm_pop = rio_open("data/wr/100m_pop_2019.tif")
#print(gm_pop.profile) # test if it opended successfully
#print(gm_pop.crs)

# open vector data and reproject to epsg27700
tweets_points = read_file("data/wr/level3-tweets-subset.shp").to_crs(epsg=27700)
gm_district = read_file("data/wr/gm-districts.shp").to_crs(epsg=27700)
#print(tweets_points.crs)
#print(gm_district.crs)



# Read the population raster only to get the shape and transform
pop_data = gm_pop.read(1)
transform = gm_pop.transform

#Create an empty raster to accumulate original point counts
naive_surface = np.zeros(pop_data.shape, dtype=float)

#ssign each original tweet point to its corresponding raster cell
for _, row in tweets_points.iterrows():
    pt = row.geometry
    r_idx, c_idx = rowcol(transform, pt.x, pt.y)

    #Prevent index out of bounds
    if 0 <= r_idx < naive_surface.shape[0] and 0 <= c_idx < naive_surface.shape[1]:
        naive_surface[r_idx, c_idx] += 1

#smoothing to generate a naive heatmap surface
naive_heatmap = gaussian(naive_surface, sigma=3, preserve_range=True)

#Plot the naive heatmap
fig, ax = subplots(1, 1, figsize=(16, 10))

#Draw heatmap
rio_show(
    naive_heatmap,
    ax=ax,
    transform=transform,
    cmap="RdYlBu_r"
)

#Overlay district boundaries
gm_district.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=0.8)

ax.set_title("Naive Heatmap from Original Tweet Points")
ax.axis("off")

#Function to generate random points within a polygon
def random_points(poly, n):
    minx, miny, maxx, maxy = poly.bounds
    points = []
    #Avoid infinite loops
    max_attempts = n* 100 
    i = 0
    while len(points)<n and i < max_attempts:
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        p = Point(x, y)
        if p.within(poly):
            points.append(p)
        i += 1
    return points

def raster_value(raster, pt):
    # rasterio.sample expects (x, y) in raster CRS
    val = next(raster.sample([(pt.x, pt.y)]))[0]

    # handle nodata
    if raster.nodata is not None and val == raster.nodata:
        return None

    # sometimes nodata can be NaN
    try:
        if val != val:  # NaN check
            return None
    except Exception:
        pass

    return float(val)

#generate random points and find the best point
def largest_point_in_polygon(poly, raster, n_candidates=20):
    #candidates is a random points list
    candidates = random_points(poly, n_candidates)
    #initiate paramemts
    best_p = None
    best_v = -float('inf')
    for p in candidates:
       v = raster_value(raster, p)
       if v is None:
           continue
       #find the largest value of point in ratser
       if v > best_v:
           best_v = v
           best_p = p       
    return best_p, best_v

#calculate r
# 0.001 for country, 0.01 for county, 1 for town and better
def radius_calculate(area, s = 0.1):
    r = ((area * s)  / math.pi)** 0.5  
    return r
       

#set a new column in tweets_points
tweets_points["district_name"] = None

# loop through each district polygon
for i, district in gm_district.iterrows():
    # get the geometry of the district
    district_geom = district.geometry
    # get the district name 
    district_name = district["NAME"]
    for j, tweet in tweets_points.iterrows():
        if tweet.geometry.within(district_geom):
            tweets_points.loc[j, "district_name"] = district_name
            
#Avoiding the warning of chained assignment
tweets_points = tweets_points.copy()

#count the number of tweets that belong to the current district
for i, district in gm_district.iterrows():
    district_name = district["NAME"]
    district_geom = district.geometry
    
# initialise a counter for the number of tweets and points series 
    count = 0
    points = []
    
    for j, tweet in tweets_points.iterrows():
        if tweet["district_name"] == district_name:
           count += 1
           points.append(tweet.geometry)
           
    #show result
    #print(district_name, count)
    #store the number of tweets
    gm_district.loc[i,"count"] = count
    
    #test
    #print(gm_district[["NAME","count"]])
    
    # store the best points of all districts
    redistributed_records = []  
    n_candidates = 10 # w = 20
    
for i, district in gm_district.iterrows():
    district_geom = district.geometry
    district_name = district['NAME']
    
    tweets_in_district = tweets_points[tweets_points["district_name"] == district_name]
    
    # evry tweet generate 20 points and find the best candidate point
    for j, tweet in tweets_in_district.iterrows():
        best_p, best_v = largest_point_in_polygon(district_geom, gm_pop, n_candidates)
        #store in redistributed_record 
        redistributed_records.append({
           "district_name": district_name,
           "tweet_id": j,
           "geometry": best_p,
           "raster_value": best_v
       })

# convert to GeoDataFrame
redistributed_df = pd.DataFrame(redistributed_records)
redistributed_gdf = gpd.GeoDataFrame(redistributed_df, geometry="geometry", crs=gm_district.crs)

# check data
#print(redistributed_gdf.head())
#print(f"Total redistributed points:, {len(redistributed_gdf)}")


#Read Population Grid
pop_data = gm_pop.read(1)
transform = gm_pop.transform

#set a new blank raster surface
output_surface  = np.zeros(pop_data.shape)

cellsize = abs(transform.a)
s = 0.01
# loop through each district area 
for i, district in gm_district.iterrows():
    district_name = district["NAME"]
    district_area = district.geometry.area
    
    #calculate r and convert it to raster
    r = radius_calculate(district_area, s)
    r_cells = int(r / cellsize)
    
    #extract the point of the current district
    points_in_admin = redistributed_gdf[redistributed_gdf["district_name"] == district_name]
    
    #loop point in list
    for _, row in points_in_admin.iterrows():
        pt = row.geometry
        
        # transform to raster from location
        r_idx, c_idx= rowcol(transform, pt.x, pt.y)
        #use skimage.draw.disk
        rr, cc = disk((r_idx, c_idx), r_cells, shape=output_surface.shape)
        #calculate distance between seed and point
        dist_cell = ((rr - r_idx) ** 2 + (cc - c_idx) ** 2)**0.5
        #Linear reduction
        value = 1 - dist_cell/r_cells
        #put value into surface
        output_surface[rr,cc] += value


# show output surface
my_fig, my_ax = subplots(1, 1, figsize=(16, 10))
gm_district.plot(ax=my_ax, facecolor="none", edgecolor="black", linewidth=0.8)
#tweets_points.plot(ax=my_ax, markersize=20, color="red", alpha=0.6, marker="x")

#set a title
my_ax.set_title("Weighted Redistribution Output Surface")

#draw raster
rio_show(
    output_surface,
    ax=my_ax,
    transform=transform,
    cmap="RdYlBu_r"
)

# overlay boundaries
gm_district.plot(ax=my_ax, facecolor="none", edgecolor="black", linewidth=0.8)

#add a colourbar 
my_fig.colorbar(
    ScalarMappable(norm=Normalize(vmin=output_surface.min(), 
                                  vmax=output_surface.max()), cmap='RdYlBu_r'),
    ax=my_ax,
    label="Accumulated weight"
)

# add scalebar
my_ax.add_artist(ScaleBar(dx=1, units="m", location="lower right"))
    
#add north arrow
x, y, arrow_length = 0.95, 0.95, 0.08

my_ax.annotate(
    'N',
    xy=(x, y),
    xytext=(x, y - arrow_length),
    arrowprops=dict(facecolor='black', width=4, headwidth=12),
    ha='center',
    va='center',
    fontsize=16,
    xycoords=my_ax.transAxes
)

# turn off the visible axes on the map and save graph to file
my_ax.axis('off')
savefig("out/tweets_heat_map.png", dpi=300, bbox_inches='tight')

# close the file
gm_pop.close()

# --- NO CODE BELOW HERE ---

# report runtime
print(f"completed in: {perf_counter() - start_time} seconds")

