namespace Challenge;

using System;
using System.Diagnostics;
using System.Collections.Frozen;
using System.Collections.Generic;
using System.Linq;


class Store
{
    private readonly object obj = new();
    private List<Action> actions = new();
    private record Entry(int Capacity, Dictionary<string, OrderRecord> Data);
    readonly FrozenDictionary<string, Entry> store;
    readonly Dictionary<string, string> storeRecord = new();

    /// <summary>
    /// Contructor for the class that initializes the store object with required capacity.
    /// </summary>
    public Store()
    {
        var data = new Dictionary<string, Entry>(3);

        void Add(string key, int capacity) =>
            data.Add(key, new Entry(capacity,
                new Dictionary<string, OrderRecord>(capacity)));

        Add(Action.Cooler, 6);
        Add(Action.Heater, 6);
        Add(Action.Shelf, 12);
        store = data.ToFrozenDictionary();
    }

    /// <summary>
    /// Private methos to place order at the final destination.
    /// </summary>
    /// <param name="destination">the final destination of the order</param>
    /// <param name="order">order to be placed</param>
    private void Place(string destination, OrderRecord order)
    {
        var entry = store[destination];
        Debug.Assert(entry.Capacity > entry.Data.Count);
        entry.Data.Add(order.Id, order);
        Log.Info("Store", $"Placed order = {order.Id} into {destination}");
        actions.Add(new Action(DateTime.Now, order.Id, Action.Place, destination));
        Debug.Assert(!storeRecord.ContainsKey(order.Id));
        storeRecord[order.Id] = destination;
    }

    /// <summary>
    /// Remove all expired orders from destination.
    /// </summary>
    /// <param name="destination">destination where the expired orders have to discarded</param>
    private void CleanExpired(string destination)
    {
        var data = store[destination].Data;
        var now = DateTime.Now;
        foreach(var order in data.Values)
            if (now > order.Expiry)
            {
                data.Remove(order.Id);
                Log.Info("Store", $"Discarded order = {order.Id} from {destination}");
                storeRecord.Remove(order.Id);
                actions.Add(new Action(DateTime.Now, order.Id, Action.Discard, destination));
            }
    }
    /// <summary>
    /// Check if the space in availble in the destination, and discard eppired orders if neccessary.
    /// </summary>
    /// <param name="destination">destination which is to be checked for availability</param>
    private bool Available(string destination)
    {
        var entry = store[destination];
        if (entry.Capacity > entry.Data.Count) return true;
        CleanExpired(destination);
        return entry.Capacity > entry.Data.Count;
    }

    private bool TryMoveFromShelf(string destination)
    {
        if (!Available(destination)) return false;
        var moveOrder = store[Action.Shelf].Data.Values.Where(o => o.Destination == destination).MinBy(o =>
                        DateTime.Now - o.Expiry);
        if (moveOrder == null) return false;
        Debug.Assert(!store[destination].Data.ContainsKey(moveOrder.Id));
        moveOrder.AdjustExpiry(Action.Shelf, destination);
        store[Action.Shelf].Data.Remove(moveOrder.Id);
        store[destination].Data.Add(moveOrder.Id, moveOrder);
        Log.Info("Store", $"Moving  order = {moveOrder.Id} from {Action.Shelf} to {destination}");
        actions.Add(new Action(DateTime.Now, moveOrder.Id, Action.Move, destination));
        Debug.Assert(storeRecord[moveOrder.Id] == Action.Shelf);
        storeRecord[moveOrder.Id] = destination;
        Debug.Assert(Available(Action.Shelf));
        return true;
    }

    /// <summary>
    // Return true if space in available in right destination of storage, else return false.
    /// <summary>
    private bool EnsureCapacity(string destination)
    {
        // If space is available in target destination or shelp, return true/false respectively.
        if (Available(destination)) return true;
        if (Available(Action.Shelf)) return false;

        // You cannot move an existing order to Hot/Cold storage since it is already full,
        // So we find the earlier expiry product from shelf and move to hot/cold
        if (destination != Action.Shelf)
            if (TryMoveFromShelf(Action.Cooler) || TryMoveFromShelf(Action.Heater))
                return false;

        // Find the order from shelp with expires earliest.
        var discardOrder = store[Action.Shelf].Data.Values.MinBy(o => DateTime.Now - o.Expiry);
        Debug.Assert(discardOrder != null); // Since shelf is full, something has to be there.
        var now = DateTime.Now;

        actions.Add(new Action(now, discardOrder.Id, Action.Discard, discardOrder.Destination));
        store[Action.Shelf].Data.Remove(discardOrder.Id);
        storeRecord.Remove(discardOrder.Id);
        Log.Info("Store", $"Discarded order = {discardOrder.Id} from {Action.Shelf}");

        Debug.Assert(Available(Action.Shelf));
        return false;
    }

    /// <summary>
    /// Place order with the store. Finds the appropriate space nad places it there.
    /// </summary>
    /// <param name="order">order to be placed</param>
    /// <param name="orderTime">Order creation time</param>
    public void PlaceOrder(Order order, DateTime orderTime)
    {
        lock (obj)
        {
            var orderRecord = new OrderRecord(order, orderTime);
            var creation = Log.DateTime(orderRecord.OrderTime);
            var expiry = Log.DateTime(orderRecord.Expiry);
            Log.Info("Store", $"For Order = {orderRecord.Id} -> Creation Time: {creation} / Expiry = {expiry}");
            var destination = EnsureCapacity(orderRecord.Destination) ? orderRecord.Destination : Action.Shelf;
            Place(destination, orderRecord);
        }
    }

    /// <summary>
    /// Pick up the order from store.
    /// </summary>
    /// <param name="id">order id to be picked up</param>
    public void PickUp(string id)
    {
        lock (obj)
        {
            string temperature = storeRecord[id];
            Debug.Assert(store[temperature].Data.ContainsKey(id));
            store[temperature].Data.Remove(id);
            storeRecord.Remove(id);
            var now = DateTime.Now;
            actions.Add(new Action(now, id, Action.Pickup, temperature));
            Log.Info("Store", $"Picked up order = {id} from {temperature} at {Log.DateTime(now)}");
        }
    }

    /// <summary>
    /// Return the immutable list of actions.
    /// </summary>
    public IReadOnlyList<Action> Actions()
    {
#if DEBUG
        int count = 0;
        lock (obj) { foreach(var value in store.Values) count += value.Data.Count; }
        Debug.Assert(count == 0, "Store is not empty!"); // Assert that the store is empty!
#endif
        return actions; // No need to use lock, as it's called at the end!
    }
}
