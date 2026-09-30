using FleetWise.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace FleetWise.Api.Controllers;

[ApiController]
[Route("api/dispatch")]
public class DispatchController : ControllerBase
{
    private readonly DispatcherService _dispatcher;
    private readonly IClock _clock;

    public DispatchController(DispatcherService dispatcher, IClock clock)
    {
        _dispatcher = dispatcher;
        _clock = clock;
    }

    [HttpGet]
    public async Task<IActionResult> GetLines()
    {
        if (!TenantContext.TryResolve(Request.Headers, out var tenant, out var error))
        {
            return BadRequest(new { error });
        }

        var lines = await _dispatcher.GetLinesAsync(tenant!.TenantId);
        return Ok(new { generatedAt = _clock.UtcNow, count = lines.Count, lines });
    }
}
