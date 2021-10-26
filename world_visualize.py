# import mplleaflet
# import matplotlib.pyplot as plt
# import networkx as nx

# pos = {u'Afghanistan': [66.00473365578554, 33.83523072784668],
#  u'Aland': [19.944009818523348, 60.23133494165451],
#  u'Albania': [20.04983396108883, 41.14244989474517],
#  u'Algeria': [2.617323009197829, 28.158938494487625],
# }

# fig, ax = plt.subplots()

# GG = nx.Graph()
# nx.draw_networkx_nodes(GG,pos=pos,node_size=10)#,node_color='red',edge_color='k',alpha=.5, with_labels=True)
# nx.draw_networkx_edges(GG,pos=pos,edge_color='gray', alpha=.1)
# nx.draw_networkx_labels(GG,pos)#, label_pos =10.3)

# #mplleaflet.display(fig=ax.figure)
# mplleaflet.show()

import cartopy.crs as ccrs
import matplotlib.pyplot as plt

ax = plt.axes(projection=ccrs.PlateCarree())
ax.stock_img()

ny_lon, ny_lat = -75, 43
delhi_lon, delhi_lat = 77.23, 28.61

plt.plot([ny_lon, delhi_lon], [ny_lat, delhi_lat],
         color='blue', linewidth=2, marker='o',
         transform=ccrs.Geodetic(),
         )

plt.plot([ny_lon, delhi_lon], [ny_lat, delhi_lat],
         color='gray', linestyle='--',
         transform=ccrs.PlateCarree(),
         )

plt.text(ny_lon - 3, ny_lat - 12, 'New York',
         horizontalalignment='right',
         transform=ccrs.Geodetic())

plt.text(delhi_lon + 3, delhi_lat - 12, 'Delhi',
         horizontalalignment='left',
         transform=ccrs.Geodetic())

plt.show()