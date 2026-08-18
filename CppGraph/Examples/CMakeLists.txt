cmake_minimum_required(VERSION 3.18)

project(GraphPlotExamples LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(GraphPlot REQUIRED)

function(add_graph_plot_example target_name)
    add_executable(${target_name} ${ARGN})
    set_target_properties(${target_name} PROPERTIES OUTPUT_NAME "${target_name}.bin")
    target_link_libraries(${target_name} PRIVATE GraphPlot::graph_plot)
endfunction()


add_graph_plot_example(histogramStatic histogramStatic.cpp)
add_graph_plot_example(histogramDynamic histogramDynamic.cpp)
add_graph_plot_example(graphStatic graphStatic.cpp)
add_graph_plot_example(graphDynamic graphDynamic.cpp)
