# Homebrew Formula for Docpistemic
# Documentation: https://docs.brew.sh/Formula-Cookbook
#
# Installation:
#   brew tap nubaeon/tap
#   brew install docpistemic

class Docpistemic < Formula
  include Language::Python::Virtualenv

  desc "Epistemic documentation coverage assessment - know what your docs know"
  homepage "https://github.com/nubaeon/docpistemic"
  url "https://files.pythonhosted.org/packages/source/d/docpistemic/docpistemic-0.1.0.tar.gz"
  sha256 "6f558a5b1ad502f1118001dc27a1cd758ce3022c8c1532f5e88e8b07cd10247b"
  license "MIT"

  depends_on "python@3.11"
  depends_on "git"

  # Runtime Python dependencies
  resource "typer" do
    url "https://files.pythonhosted.org/packages/source/t/typer/typer-0.9.0.tar.gz"
    sha256 "50922fd79aea2f4751a8e0408ff10d2662bd0c8bbfa84755a699f3bada2978b2"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "5cb5123b5cf9ee70584244246816e9114227e0b98ad9176eede6ad54bf5403fa"
  end

  resource "gitpython" do
    url "https://files.pythonhosted.org/packages/source/g/gitpython/GitPython-3.1.40.tar.gz"
    sha256 "22b126e9ffb671fdd0c129796343a02bf67bf2994b35449ffc9321aa755e18a4"
  end

  # empirica is a dependency - this is the trojan horse :)
  resource "empirica" do
    url "https://files.pythonhosted.org/packages/source/e/empirica/empirica-1.2.3.tar.gz"
    sha256 "39828bc0bbb94bc9cc6a8c53739897b1bf7965dbf80bdd8fe3ac54e84e8e247d"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    # Test that the CLI works
    assert_match "0.1.0", shell_output("#{bin}/docpistemic version")

    # Test that assess command exists
    system "#{bin}/docpistemic", "assess", "--help"
  end
end
