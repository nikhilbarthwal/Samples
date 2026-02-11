namespace Challenge;

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;


/// <summary>
/// Delivery is a class that simulates item delivery.
/// </summary>
class Delivery
{
    readonly TimeSpan timer = TimeSpan.FromMicroseconds(100);
    CancellationTokenSource cts = new ();
    readonly TimeSpan Min;
    readonly TimeSpan Max;
    ConcurrentDictionary<string,  DateTime> deliveries = new ConcurrentDictionary<string, DateTime>();

    /// <summary>
    /// DeliveryLoop is a infite loop that keeps polling orders for which the
    /// delivery time is hit and then notifies Store of pick up.
    /// </summary>
    /// <param name="store">Store Instance</param>
    private void DeliveryLoop(Store store)
    {
        Log.Info("Delivery", "Starting the delivery loop");
        while(!cts.IsCancellationRequested)
        {
            var now = DateTime.Now;
            foreach (KeyValuePair<string, DateTime> entry in deliveries)
                if (now > entry.Value)
                    if (deliveries.TryRemove(entry))
                        store.PickUp(entry.Key);
                    else
                        Log.Error("Delivery", $"Unable to Pick up Order Id = {entry.Key} from Store");
            Thread.Sleep(timer);
        }

        Debug.Assert(deliveries.IsEmpty, "Deliveries are still pending!"); // Assert that all deliveries are completed!
        Log.Info("Delivery", "Closed the  delivery, all orders processed!");
    }

    /// <summary>
    /// Constructor for the class. It creates the timespan and starts the deliver loop.
    /// </summary>
    /// <param name="store">Store Instance</param>
    /// <param name="min">Min for delivery time</param>
    /// <param name="min">Min for delivery time</param>
    public Delivery(Store store, int min, int max)
    {
        Min = TimeSpan.FromSeconds(min);
        Max = TimeSpan.FromSeconds(max);
        Task.Run(() => DeliveryLoop(store));
    }

    /// <summary>
    /// Wait for the maximum amount of time after last order for deliveries to complete and stop the poll thread.
    /// <summary>
    public void Stop()
    {
        Thread.Sleep(Max);
        cts.Cancel();
    }

    /// <summary>
    /// Notify to delivery system that a new order has arrived. This will create a random delivery time between
    /// min and max.
    /// <summary>
    /// <param name="orderId">Order Id for the new order</param>
    /// <param name="orderTime">Order creation time</param>
    public void Notify(string orderId, DateTime orderTime)
    {
        var randomTicks = Random.Shared.NextInt64(Min.Ticks, Max.Ticks);
        var delivery = orderTime + new TimeSpan(randomTicks);
        if (deliveries.TryAdd(orderId, delivery))
            Log.Info("Delivery", $"Added delivery time of {Log.DateTime(delivery)} for order Id = {orderId}");
        else
            Log.Error("Delivery", $"Unable to add delivery time for order Id = {orderId}");
    }
}
