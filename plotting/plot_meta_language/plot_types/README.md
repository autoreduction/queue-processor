### Plot types
Plots are defined in custom `.yaml` files. These files should describe the meta data of the plot
including the type of plot and it's axis scaling, units, and titles. An `example.yaml` file is 
supplied in this directory for reference.
Below are valid inputs for the meta data fields:
```yaml
figure.type: [line, scatter, marker, line+marker]
figure.opacity: "float"

figure.x_axis.title: "string"
figure.x_axis.unit: "string"
figure.x_axis.type: [log, linear]

figure.y_axis.title: "string"
figure.y_axis.unit: "string"
figure.y_axis.type: [log, linear]
```

*Note: that strings are able to take LaTeX arguments if delimited with `$` e.g. `$ \gamma $`*

Any `*.yaml` files in this directory (except `example.yaml`) are considered to be valid 
plot types and are therefore offered to the user at run time. the name displayed to the user is the 
same as the file e.g. `example.yaml` will be displayed as `plot_type: example`.

These files are only responsible for the layout of the plots, not the actual data lines/scatter/etc.
Data should be handled by the plot handler as the customisation is limited.
