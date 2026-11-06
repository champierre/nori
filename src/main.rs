use clap::Parser;
use std::io::{self, BufRead};
use std::path::{Path, PathBuf};
use std::process::ExitCode;

/// Merges PDF files into one.
#[derive(Parser)]
#[command(version, about)]
struct Cli {
    /// Output file. Overwritten if it exists.
    #[arg(short, long, value_name = "FILE")]
    output: PathBuf,

    /// File listing input PDFs, one path per line, appended after the
    /// positional inputs. "-" reads the list from standard input.
    #[arg(long, value_name = "FILE")]
    list: Option<PathBuf>,

    /// Inputs parsed at once, on separate threads. Faster on inputs with
    /// many objects; holds up to about twice this many inputs in memory.
    #[arg(short, long, value_name = "N", default_value_t = 1, value_parser = clap::value_parser!(u16).range(1..))]
    jobs: u16,

    /// Input PDFs, merged in this order.
    #[arg(value_name = "PDF")]
    inputs: Vec<PathBuf>,
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let mut inputs = cli.inputs;
    if let Some(list) = &cli.list {
        match read_list(list) {
            Ok(paths) => inputs.extend(paths),
            Err(e) => return fail(&format!("{}: {e}", list.display())),
        }
    }
    if inputs.is_empty() {
        return fail("no input files");
    }
    if inputs.iter().any(|input| same_file(input, &cli.output)) {
        return fail("the output must not be one of the inputs");
    }
    match nori::merge(&inputs, &cli.output, usize::from(cli.jobs)) {
        Ok(_) => ExitCode::SUCCESS,
        Err(e) => fail(&e.to_string()),
    }
}

fn read_list(path: &Path) -> io::Result<Vec<PathBuf>> {
    let reader: Box<dyn BufRead> = if path == Path::new("-") {
        Box::new(io::stdin().lock())
    } else {
        Box::new(io::BufReader::new(std::fs::File::open(path)?))
    };
    let mut paths = Vec::new();
    for line in reader.lines() {
        let line = line?;
        let line = line.trim_end_matches('\r');
        if !line.is_empty() {
            paths.push(PathBuf::from(line));
        }
    }
    Ok(paths)
}

fn same_file(a: &Path, b: &Path) -> bool {
    match (a.canonicalize(), b.canonicalize()) {
        (Ok(a), Ok(b)) => a == b,
        _ => a == b,
    }
}

fn fail(message: &str) -> ExitCode {
    eprintln!("nori: {message}");
    ExitCode::from(1)
}
