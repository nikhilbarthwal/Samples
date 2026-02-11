using System;
using System.Threading.Tasks;

namespace Challenge;

class Challenge
{
    /// <summary>
    /// Challenge harness
    /// </summary>
    /// <param name="auth">Authentication token (required)</param>
    /// <param name="endpoint">Problem server endpoint</param>
    /// <param name="name">Problem name. Leave blank (optional)</param>
    /// <param name="seed">Problem seed (random if zero)</param>
    /// <param name="rate">Inverse order rate (in milliseconds)</param>
    /// <param name="min">Minimum pickup time (in seconds)</param>
    /// <param name="max">Maximum pickup time (in seconds)</param>
    static async Task Main(string auth, string endpoint = "https://api.cloudkitchens.com", string name = "",
                           long seed = 0, int rate = 500, int min = 4, int max = 8)
    {
        try
        {
            var client = new Client(endpoint, auth);
            var problem = await client.NewProblemAsync(name, seed);

            var store = new Store(); // Object to mimic Store.
            var delivery = new Delivery(store, min, max); // Object that would handle deliveries.

            foreach (var order in problem.Orders)
            {
                Log.Info("Main", $"Received Order = {order}");
                var now = DateTime.Now;
                store.PlaceOrder(order, now);
                delivery.Notify(order.Id, now);
                await Task.Delay(rate);
            }
            delivery.Stop(); // Stop the deliveries and close the delivery thread.

            var result = await client.SolveAsync(problem.TestId, TimeSpan.FromMilliseconds(rate),
                         TimeSpan.FromSeconds(min), TimeSpan.FromSeconds(max), store.Actions());
            Log.Info("Result", result);
        }
        catch (Exception e)
        {
            Log.Error("Result", $"Simulation failed: {e}");
        }
    }
}
