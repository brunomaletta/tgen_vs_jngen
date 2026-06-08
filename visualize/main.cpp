#include <iostream>
#include <string>

void run_tgen_samples(const std::string &out_dir);
void run_jngen_samples(const std::string &out_dir);

int main(int argc, char **argv) {
	std::string out_dir = "results/svg";
	if (argc > 1)
		out_dir = argv[1];

	std::cout << "Writing samples to " << out_dir << '\n';
	run_tgen_samples(out_dir);
	run_jngen_samples(out_dir);
	return 0;
}
