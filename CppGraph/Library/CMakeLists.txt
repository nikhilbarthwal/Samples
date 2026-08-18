cmake_minimum_required(VERSION 3.18)

project(GraphPlot VERSION 1.0.0 LANGUAGES CXX)

set(PREFIX "/usr/local" CACHE PATH "Package install prefix")
set(CMAKE_INSTALL_PREFIX "${PREFIX}" CACHE PATH "Install prefix" FORCE)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets)
set(QT_WIDGETS_LIB Qt6::Widgets)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_library(graph_plot STATIC
    graph.h
    histogram.h
    common.h
    common.cpp
    graph.cpp
    histogram.cpp
)

target_include_directories(graph_plot
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_link_libraries(graph_plot
    PUBLIC
        ${QT_WIDGETS_LIB}
)

set_target_properties(graph_plot PROPERTIES
    OUTPUT_NAME graph_plot
)

install(TARGETS graph_plot
    EXPORT GraphPlotTargets
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

install(FILES graph.h histogram.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(EXPORT GraphPlotTargets
    FILE GraphPlotTargets.cmake
    NAMESPACE GraphPlot::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/GraphPlot
)

configure_package_config_file(
    GraphPlotConfig.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/GraphPlotConfig.cmake"
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/GraphPlot
)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/GraphPlotConfigVersion.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/GraphPlotConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/GraphPlotConfigVersion.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/GraphPlot
)
