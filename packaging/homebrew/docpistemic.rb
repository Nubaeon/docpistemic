# Homebrew Formula for Docpistemic
# Install: brew install docpistemic.rb

class Docpistemic < Formula
  include Language::Python::Virtualenv

  desc "Epistemic documentation coverage assessment"
  homepage "https://github.com/Nubaeon/docpistemic"
  url "https://files.pythonhosted.org/packages/source/d/docpistemic/docpistemic-0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.11"
  depends_on "git"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "0.1.0", shell_output("#{bin}/docpistemic version")
  end
end
