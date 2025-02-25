package lgr_test

import (
	"testing"

	"github.com/WLM1ke/poptimizer/data/pkg/lgr"
)

const (
	_testFormat = "format %s,\t%d,%f\n"
	_testMsg    = `benchmark sample message blow`
	_testInt    = 9999
	_testFloat  = 10.10
)

type MockWriter struct{}

func (m MockWriter) Write(b []byte) (int, error) {
	_ = b

	return 0, nil
}

func BenchmarkLogger(b *testing.B) {
	logger := lgr.WithOptions(
		lgr.Name("test"),
		lgr.Writer(MockWriter{}),
		lgr.TimeWithSeconds(),
	)

	b.ReportAllocs()
	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			logger.Infof(_testFormat, _testMsg, _testInt, _testFloat)
			logger.Warnf(_testFormat, _testMsg, _testInt, _testFloat)

			logger.Infof(_testFormat, _testMsg, _testInt, _testFloat)
			logger.Warnf(_testFormat, _testMsg, _testInt, _testFloat)

			logger.Infof(_testFormat, _testMsg, _testInt, _testFloat)
			logger.Warnf(_testFormat, _testMsg, _testInt, _testFloat)
		}
	})
}

// BenchmarkLogger         537844              2245 ns/op               0 B/op          0 allocs/op
// BenchmarkLogger         623455              2271 ns/op               0 B/op          0 allocs/op
// BenchmarkLogger         662754              2295 ns/op               0 B/op          0 allocs/op
// BenchmarkLogger         625706              2358 ns/op               0 B/op          0 allocs/op
// BenchmarkLogger         625076              2291 ns/op               0 B/op          0 allocs/op
