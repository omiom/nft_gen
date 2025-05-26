#!/usr/bin/env python3
"""
NFT Metadata Generator - Command Line Interface
"""
import argparse
import sys
import os

# Attempt to import from src, assuming standard project structure
try:
    from .pre_validator import PreValidator, load_yaml_config
    from .generator import Generator
    from .exporter import Exporter
    from .models import Token # Assuming Token will be in models.py
except ImportError:
    # Fallback if running script directly from src or tests without proper PYTHONPATH
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.pre_validator import PreValidator, load_yaml_config
    from src.generator import Generator
    from src.exporter import Exporter
    from src.models import Token


def handle_generate_command(args):
    """Handles the 'generate' command logic."""
    print("Starting NFT Metadata Generation Process...")
    print(f"  Seed: {args.seed}")
    print(f"  Numerology File: {args.numerology}")
    print(f"  Rules File: {args.rules}")
    print(f"  Output Directory Base: {args.output_dir}")
    if args.relaxed_tolerance:
        print("  Relaxed Tolerance: Enabled")
    if args.prioritize_sets:
        print("  Prioritize Sets: Enabled")

    try:
        # 1. Load Configurations
        print("\nStep 1: Loading configuration files...")
        numerology_config = load_yaml_config(args.numerology)
        rules_config = load_yaml_config(args.rules)
        print("  Configuration files loaded successfully.")

        # 2. Pre-Validate Configurations
        print("\nStep 2: Pre-validating configurations...")
        validator = PreValidator(numerology_config, rules_config)
        validation_results = validator.validate()
        if validation_results != ["Configuration Valid"]:
            print("  Configuration validation failed:")
            for error in validation_results:
                print(f"    - {error}")
            sys.exit(1)
        print("  Configurations are valid.")

        # 3. Generate Tokens
        # TODO: Pass args.relaxed_tolerance and args.prioritize_sets to Generator
        #       once those features are implemented in the Generator.
        print("\nStep 3: Generating tokens...")
        generator = Generator(
            numerology_config=numerology_config,
            rules_config=rules_config,
            seed=args.seed
        )
        
        # Generator is expected to return List[Token] from src.models
        generated_tokens: List[Token] = generator.generate_tokens()
        
        print(f"  Successfully generated {len(generated_tokens)} tokens.")

        # 4. Export Tokens
        print("\nStep 4: Exporting tokens...")
        exporter = Exporter(output_dir_base=args.output_dir)
        
        # Get category order for CSV from numerology_config
        numerology_categories = list(numerology_config.get('categories', {}).keys())
        
        exporter.export_tokens(generated_tokens, numerology_categories)
        print("  Tokens exported successfully.")

        print("\nNFT Metadata Generation Process Completed Successfully!")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="NFT Metadata Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # --- Generate Command ---
    generate_parser = subparsers.add_parser("generate", help="Generate NFT metadata")
    generate_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for deterministic generation (default: 0)."
    )
    generate_parser.add_argument(
        "--numerology",
        type=str,
        default="numerology.yaml",
        help="Path to the numerology YAML file (default: numerology.yaml)."
    )
    generate_parser.add_argument(
        "--rules",
        type=str,
        default="rules.yaml",
        help="Path to the rules YAML file (default: rules.yaml)."
    )
    generate_parser.add_argument(
        "--relaxed_tolerance",
        action="store_true",
        help="Use relaxed tolerance during generation (default: False)."
    )
    generate_parser.add_argument(
        "--prioritize_sets",
        action="store_true",
        help="Prioritize completing sets during generation (default: False)."
    )
    generate_parser.add_argument(
        "--output_dir",
        type=str,
        default="output",
        help="Base directory for output files (default: output)."
    )
    generate_parser.set_defaults(func=handle_generate_command)
    
    # --- (Future commands can be added here) ---
    # validate_parser = subparsers.add_parser("validate", help="Validate configuration files")
    # validate_parser.add_argument(...)
    # validate_parser.set_defaults(func=handle_validate_command)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help() # Should not happen if a command is required

if __name__ == "__main__":
    main()