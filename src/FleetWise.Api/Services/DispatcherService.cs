using FleetWise.Api.Data;
using FleetWise.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace FleetWise.Api.Services;

/// <summary>
/// Overdue maintenance dispatcher (spec 001). Every method takes the tenant explicitly
/// and scopes every query by it (constitution Principle II).
/// </summary>
public class DispatcherService
{
    private const int DueSoonDays = 7;

    private readonly FleetWiseDbContext _db;
    private readonly IClock _clock;

    public DispatcherService(FleetWiseDbContext db, IClock clock)
    {
        _db = db;
        _clock = clock;
    }

    /// <summary>US1: vehicles of this tenant with a scheduled service overdue or due within 7 days.</summary>
    public async Task<List<DispatchLine>> GetLinesAsync(int tenantId)
    {
        var today = _clock.UtcNow.Date;

        var vehicles = await _db.Vehicles.AsNoTracking()
            .Where(v => v.TenantId == tenantId)
            .ToListAsync();
        var schedules = await _db.MaintenanceSchedules.AsNoTracking().ToListAsync();
        var records = await _db.MaintenanceRecords.AsNoTracking()
            .Where(r => r.TenantId == tenantId)
            .ToListAsync();
        var openWorkOrders = await _db.WorkOrders.AsNoTracking()
            .Where(w => w.TenantId == tenantId && (w.Status == WorkOrderStatus.Draft || w.Status == WorkOrderStatus.Scheduled))
            .Select(w => new { w.VehicleId, w.ServiceType })
            .ToListAsync();

        var lines = new List<DispatchLine>();
        foreach (var vehicle in vehicles)
        {
            foreach (var schedule in schedules.Where(s => s.VehicleClass == vehicle.VehicleClass))
            {
                var last = records
                    .Where(r => r.VehicleId == vehicle.Id && r.ServiceType == schedule.ServiceType)
                    .OrderByDescending(r => r.PerformedOn)
                    .FirstOrDefault();

                DispatchStatus status;
                DispatchTrigger trigger;
                int? kmOverdue = null;
                int daysUntilDue;

                if (last is null)
                {
                    status = DispatchStatus.Overdue;
                    trigger = DispatchTrigger.NoHistory;
                    daysUntilDue = 0;
                }
                else
                {
                    var kmSince = vehicle.OdometerKm - last.OdometerKm;
                    var daysSince = (int)(today - last.PerformedOn.Date).TotalDays;
                    daysUntilDue = schedule.IntervalDays - daysSince;

                    if (kmSince > schedule.IntervalKm)
                    {
                        status = DispatchStatus.Overdue;
                        trigger = DispatchTrigger.Distance;
                        kmOverdue = kmSince - schedule.IntervalKm;
                    }
                    else if (daysUntilDue < 0)
                    {
                        status = DispatchStatus.Overdue;
                        trigger = DispatchTrigger.Date;
                    }
                    else if (daysUntilDue <= DueSoonDays)
                    {
                        status = DispatchStatus.DueSoon;
                        trigger = DispatchTrigger.Date;
                    }
                    else
                    {
                        continue;
                    }
                }

                if (openWorkOrders.Any(w => w.VehicleId == vehicle.Id && w.ServiceType == schedule.ServiceType))
                {
                    status = DispatchStatus.AlreadyHandled;
                }

                lines.Add(new DispatchLine(vehicle.Id, vehicle.UnitNumber, schedule.ServiceType, status, trigger, kmOverdue, daysUntilDue, Suggestion: null));
            }
        }

        return lines
            .OrderBy(l => l.Status)
            .ThenByDescending(l => l.KmOverdue ?? 0)
            .ThenBy(l => l.DaysUntilDue)
            .ToList();
    }
}
