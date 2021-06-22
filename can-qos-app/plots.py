#!/usr/bin/env python
from matplotlib import pyplot as plt


# Auxiliary functions used to generates plots
def generate_link_utilization_plot(json_data, threshold=0.25):
    """Parses JSON data and plots the interface utilization against time steps for generated traffic."""
    parsed_data = {}
    plot_interface = {}

    # Initialize parsed_data
    for time_step in json_data:
        for interface in time_step:
            parsed_data[interface['interface_name']] = {}
            plot_interface[interface['interface_name']] = False
    for key, _ in parsed_data.items():
        for time_step in range(len(json_data)):
            parsed_data[key][time_step] = 0.0

    # Populate parsed_data
    for idx, time_step in enumerate(json_data):
        for interface in time_step:
            parsed_data[interface['interface_name']][idx] = interface['utilization']
            if interface['utilization'] > threshold:
                plot_interface[interface['interface_name']] = True

    # Generate plot
    fig, ax = plt.subplots(figsize=(10, 4), dpi=80)
    for interface in [*parsed_data.keys()]:
        if plot_interface[interface]:
            ax.plot([*parsed_data[interface].keys()], [*parsed_data[interface].values()], linewidth=2, label=interface)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_xlim(0, 50)  # change upper limit as needed
    ax.set_ylim(0, 1)
    ax.grid(axis='y', color='w')
    ax.set_xlabel('Time Steps [seconds]')
    ax.set_ylabel('Interface Utilization')
    ax.set_facecolor('#f1f1f2')
    ax.legend()
    ax.show()
