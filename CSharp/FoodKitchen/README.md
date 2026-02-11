# README

Author: `Nikhil Barthwal`

## How to run

The `Dockerfile` defines a self-contained C# reference environment.
Build and run the program using [Docker](https://docs.docker.com/get-started/get-docker/):
```
$ docker build -t challenge .
$ docker run --rm -it challenge --auth <token>
```
Feel free to modify the `Dockerfile` as you see fit.

If dotnet `10.0` or later is locally installed, run the program directly for convenience:
```
$ cd Challenge
$ dotnet run -- --auth <token>
```

## Discard criteria

There are 2 main classes added here. The first one is `Deliverty`. This simulates the delivery mechanism. There are
3 primary tasks of this class:

- Create a random delivery,between min and max, time for order, once it has been notified that a new orider has arrived.
- Poll at a fixed frequency and if the current time exceeds delivery time, then notify the store for pickup.
- Stop the loop, after a pause to ensure all deliveries are completed.

Next class is the `Store` class which is simulates the store. It has 2 main function:

- Pick up orders when notified by Delivery system.
- Places the order on storage based on availability and desired storage.

It keeps a list of actions that it does and returns the immutable list at the end. A third class `OrderRecord` is
provided which keeps track of expiry and makes adjustments of the order has been moved between various destinations.
