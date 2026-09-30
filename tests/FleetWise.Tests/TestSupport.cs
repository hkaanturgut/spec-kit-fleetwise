using FleetWise.Api.Data;
using FleetWise.Api.Services;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;

namespace FleetWise.Tests;

public sealed class FixedClock : IClock
{
    public FixedClock(DateTime utcNow) => UtcNow = utcNow;
    public DateTime UtcNow { get; set; }
}

/// <summary>
/// A real SQLite database in memory, seeded with the demo data. One per test.
/// </summary>
public sealed class TestDatabase : IDisposable
{
    private readonly SqliteConnection _connection;

    public TestDatabase()
    {
        _connection = new SqliteConnection("Data Source=:memory:");
        _connection.Open();
        Clock = new FixedClock(new DateTime(2026, 10, 1, 12, 0, 0, DateTimeKind.Utc));
        var options = new DbContextOptionsBuilder<FleetWiseDbContext>().UseSqlite(_connection).Options;
        Db = new FleetWiseDbContext(options);
        Db.Database.EnsureCreated();
        SeedData.Seed(Db, Clock);
        Db.ChangeTracker.Clear();
    }

    public FleetWiseDbContext Db { get; }
    public FixedClock Clock { get; }

    public void Dispose()
    {
        Db.Dispose();
        _connection.Dispose();
    }
}
