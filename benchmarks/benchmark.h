#pragma once

#include <algorithm>
#include <cmath>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <vector>

#include <signal.h>
#include <sys/wait.h>

namespace benchmark {

using clock = std::chrono::steady_clock;

struct LibraryResult {
	double median_ms = 0;
	std::vector<double> runs_ms;
	std::string status = "ok";
	std::string error;
};

struct CaseResult {
	std::string id;
	std::string name;
	std::string name_suffix;
	std::string params;
	bool compare_both = true;
	LibraryResult tgen;
	LibraryResult jngen;
	double ratio = 0;
};

struct Report {
	std::string generated_at;
	std::string compiler;
	std::string flags;
	std::string hostname;
	std::string vendor_tgen;
	std::string vendor_jngen;
	std::vector<CaseResult> results;
};

struct CaseSpec {
	std::string id;
	std::string name;
	std::string name_suffix;
	std::string params;
	bool compare_both;
};

using CaseFn = std::function<void()>;

constexpr double kMaxRunMs = 5000.0;
constexpr int kTimedRuns = 3;

inline double elapsed_ms(clock::time_point start) {
	return std::chrono::duration<double, std::milli>(clock::now() - start)
		.count();
}

inline double median(std::vector<double> values) {
	if (values.empty())
		return 0;
	std::sort(values.begin(), values.end());
	return values[values.size() / 2];
}

constexpr size_t kChildErrorMax = 4096;

inline void read_child_error(int fd, std::string &out) {
	out.clear();
	char buf[512];
	while (out.size() < kChildErrorMax) {
		const ssize_t n = read(fd, buf, sizeof(buf));
		if (n <= 0)
			break;
		out.append(buf, buf + n);
	}
	if (out.size() > kChildErrorMax)
		out.resize(kChildErrorMax);
}

inline void write_child_error(int fd, const char *msg) {
	if (!msg || !*msg)
		return;
	const size_t len = std::strlen(msg);
	const size_t n = std::min(len, kChildErrorMax);
	(void)write(fd, msg, n);
}

// Runs @p fn in a child process and kills it if it exceeds @p max_ms wall time.
// On exception in the child, the message is read into @p child_error.
inline bool run_timed_child(const CaseFn &fn, double max_ms, double &out_ms,
							std::string &child_error) {
	child_error.clear();
	int pipefd[2];
	if (pipe(pipefd) != 0)
		throw std::runtime_error("benchmark: pipe failed");

	const auto start = clock::now();
	const pid_t pid = fork();
	if (pid < 0)
		throw std::runtime_error("benchmark: fork failed");

	if (pid == 0) {
		close(pipefd[0]);
		try {
			fn();
		} catch (const std::exception &e) {
			write_child_error(pipefd[1], e.what());
			close(pipefd[1]);
			_exit(2);
		} catch (...) {
			write_child_error(pipefd[1], "unknown exception");
			close(pipefd[1]);
			_exit(2);
		}
		close(pipefd[1]);
		_exit(0);
	}

	close(pipefd[1]);

	const auto deadline = start + std::chrono::duration_cast<clock::duration>(
								  std::chrono::duration<double, std::milli>(
									  max_ms));

	int status = 0;
	while (true) {
		const pid_t waited = waitpid(pid, &status, WNOHANG);
		if (waited == pid) {
			out_ms = elapsed_ms(start);
			if (WIFEXITED(status) && WEXITSTATUS(status) == 0) {
				close(pipefd[0]);
				return true;
			}
			if (WIFEXITED(status) && WEXITSTATUS(status) == 2) {
				read_child_error(pipefd[0], child_error);
				close(pipefd[0]);
				if (child_error.empty())
					child_error = "unknown exception";
				throw std::runtime_error(child_error);
			}
			close(pipefd[0]);
			throw std::runtime_error("benchmark: case failed in child");
		}
		if (waited < 0) {
			close(pipefd[0]);
			throw std::runtime_error("benchmark: waitpid failed");
		}
		if (clock::now() >= deadline) {
			kill(pid, SIGKILL);
			waitpid(pid, &status, 0);
			close(pipefd[0]);
			out_ms = elapsed_ms(start);
			return false;
		}
		std::this_thread::sleep_for(std::chrono::milliseconds(10));
	}
}

inline LibraryResult run_library_case(const CaseFn &fn) {
	LibraryResult result;
	try {
		for (int i = 0; i < kTimedRuns; ++i) {
			double ms = 0;
			std::string child_error;
			if (!run_timed_child(fn, kMaxRunMs, ms, child_error)) {
				result.status = "timeout";
				result.error = "single run exceeded 5000 ms limit";
				return result;
			}
			result.runs_ms.push_back(ms);
		}
		result.median_ms = median(result.runs_ms);
	} catch (const std::exception &e) {
		result.status = "error";
		result.error = e.what();
	} catch (...) {
		result.status = "error";
		result.error = "unknown exception";
	}
	return result;
}

inline std::string json_escape(const std::string &s) {
	std::string out;
	out.reserve(s.size());
	for (char c : s) {
		switch (c) {
		case '\\':
			out += "\\\\";
			break;
		case '"':
			out += "\\\"";
			break;
		case '\n':
			out += "\\n";
			break;
		case '\r':
			out += "\\r";
			break;
		case '\t':
			out += "\\t";
			break;
		default:
			out += c;
		}
	}
	return out;
}

inline std::string format_ms(double ms) {
	char buf[32];
	std::snprintf(buf, sizeof(buf), "%.3f", ms);
	std::string out(buf);
	while (!out.empty() && out.back() == '0')
		out.pop_back();
	if (!out.empty() && out.back() == '.')
		out.pop_back();
	return out.empty() ? "0" : out;
}

inline std::string iso_timestamp() {
	std::time_t now = std::time(nullptr);
	std::tm tm_buf{};
#if defined(_WIN32)
	gmtime_s(&tm_buf, &now);
#else
	gmtime_r(&now, &tm_buf);
#endif
	char buf[32];
	std::strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tm_buf);
	return buf;
}

inline std::string hostname() {
	char buf[256];
	if (gethostname(buf, sizeof(buf)) != 0)
		return "unknown";
	return buf;
}

inline void write_library_json(std::ofstream &out, const LibraryResult &r) {
	out << "      \"status\": \"" << json_escape(r.status) << "\"";
	if (!r.error.empty())
		out << ",\n      \"error\": \"" << json_escape(r.error) << "\"";
	if (r.status == "ok") {
		out << ",\n      \"median_ms\": " << format_ms(r.median_ms) << ",\n";
		out << "      \"runs_ms\": [";
		for (size_t j = 0; j < r.runs_ms.size(); ++j) {
			if (j)
				out << ", ";
			out << format_ms(r.runs_ms[j]);
		}
		out << "]";
	}
}

inline void write_json(const Report &report, const std::string &path) {
	std::ofstream out(path);
	if (!out)
		throw std::runtime_error("benchmark: cannot write " + path);

	out << "{\n";
	out << "  \"generated_at\": \"" << json_escape(report.generated_at)
		<< "\",\n";
	out << "  \"compiler\": \"" << json_escape(report.compiler) << "\",\n";
	out << "  \"flags\": \"" << json_escape(report.flags) << "\",\n";
	out << "  \"hostname\": \"" << json_escape(report.hostname) << "\",\n";
	out << "  \"vendors\": {\n";
	out << "    \"tgen\": \"" << json_escape(report.vendor_tgen) << "\",\n";
	out << "    \"jngen\": \"" << json_escape(report.vendor_jngen) << "\"\n";
	out << "  },\n";
	out << "  \"results\": [\n";

	for (size_t i = 0; i < report.results.size(); ++i) {
		const auto &r = report.results[i];
		out << "    {\n";
		out << "      \"id\": \"" << json_escape(r.id) << "\",\n";
		out << "      \"name\": \"" << json_escape(r.name) << "\",\n";
		out << "      \"name_suffix\": \"" << json_escape(r.name_suffix)
			<< "\",\n";
		out << "      \"params\": \"" << json_escape(r.params) << "\",\n";
		out << "      \"compare_both\": "
			<< (r.compare_both ? "true" : "false") << ",\n";
		out << "      \"tgen\": {\n";
		write_library_json(out, r.tgen);
		out << "\n      },\n";
		out << "      \"jngen\": {\n";
		write_library_json(out, r.jngen);
		out << "\n      }";
		if (r.compare_both && r.tgen.status == "ok" && r.jngen.status == "ok" &&
			r.jngen.median_ms > 0)
			out << ",\n      \"ratio\": " << r.ratio;
		out << "\n    }";
		if (i + 1 < report.results.size())
			out << ",";
		out << "\n";
	}

	out << "  ]\n";
	out << "}\n";
}

} // namespace benchmark
