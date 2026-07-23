let
    Source = Json.Document(
        Web.Contents(
            "https://operations-kpi-automation-demo.vercel.app/api/kpis",
            [Headers = [Accept = "application/json"]]
        )
    ),
    Teams = Source[teams],
    AsTable = Table.FromRecords(Teams),
    Typed = Table.TransformColumnTypes(
        AsTable,
        {
            {"team", type text},
            {"orders", Int64.Type},
            {"revenue_eur", Currency.Type},
            {"on_time_rate", Percentage.Type},
            {"avg_processing_hours", type number},
            {"incidents", Int64.Type}
        }
    ),
    NormalizePercentage = Table.TransformColumns(
        Typed,
        {{"on_time_rate", each _ / 100, Percentage.Type}}
    )
in
    NormalizePercentage
