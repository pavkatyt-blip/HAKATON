package task

type PIIStats struct {
	Phones    int `json:"phones"`
	Passports int `json:"passports"`
	INN       int `json:"inn"`
	SNILS     int `json:"snils"`
	Emails    int `json:"emails"`
	Addresses int `json:"addresses"`
	Persons   int `json:"persons"`
}

func BuildPIIStats(spans []PIISpan) PIIStats {
	stats := PIIStats{}

	for _, span := range spans {
		switch span.Type {
		case "PHONE":
			stats.Phones++
		case "PASSPORT":
			stats.Passports++
		case "INN":
			stats.INN++
		case "SNILS":
			stats.SNILS++
		case "EMAIL":
			stats.Emails++
		case "ADDRESS":
			stats.Addresses++
		case "PERSON":
			stats.Persons++
		}
	}

	return stats
}
