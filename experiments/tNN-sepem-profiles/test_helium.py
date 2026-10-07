"""Small deterministic checks; never opens or simulates the full RDS series."""
import hashlib
from contextlib import contextmanager
import json
import math
from pathlib import Path
import shutil
import uuid
import unittest
from unittest.mock import patch
import numpy as np
import helium as he


@contextmanager
def small_fixture_directory():
    # Windows sandbox identity cannot traverse Python's mode-0700 mkdtemp
    # directories. A unique normal-mode test directory has inherited ACLs.
    base = (he.HERE/".cache").resolve()
    base.mkdir(exist_ok=True)
    root = base/("helium-fixture-"+uuid.uuid4().hex)
    root.mkdir()
    try:
        yield root
    finally:
        if root.resolve().parent != base or not root.name.startswith("helium-fixture-"):
            raise RuntimeError("Refusing cleanup outside the exact test fixture")
        shutil.rmtree(root)


class HeliumChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response = he.HeliumResponse()

    def test_saved_source_hashes_and_grid(self):
        manifest = json.loads((he.HERE/"inputs/astar_manifest.json").read_text())
        for table in manifest["tables"]:
            source = he.HERE/"inputs"/table["derived_csv"]
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), table["derived_csv_sha256"])
            self.assertEqual(table["rows"], 121)
            self.assertEqual(table["total_energy_MeV"], [.001, 1000.])
            self.assertEqual(table["energy_MeV_per_nucleon"], [.00025, 250.])
            a = np.genfromtxt(source, delimiter=",", names=True)
            # NIST prints four significant digits independently for all
            # three columns. Use their summed half-last-digit uncertainty,
            # not an empirically widened relative tolerance.
            e, n, t = [a[k] for k in ("electronic_stopping_mev_cm2_g",
                                       "nuclear_stopping_mev_cm2_g", "total_stopping_mev_cm2_g")]
            rounding = sum(.5*10**(np.floor(np.log10(v))-3) for v in (e, n, t))
            self.assertTrue(np.all(np.abs(e+n-t) <= rounding+1e-11))

    def test_zero_channels_remain_valid(self):
        f = np.zeros((3, 8))
        output = self.response.calculate(f)
        for values in output.values():
            np.testing.assert_array_equal(values, 0.)
        f[1, 5], f[2, 6] = 1., 2.
        for values in self.response.calculate(f).values():
            self.assertTrue(np.all(np.isfinite(values)))
            self.assertTrue(np.all(values >= 0))
        x = math.sqrt(he.ENERGY[2]*he.ENERGY[3])
        f = np.zeros((1, 8))
        f[0, 3] = 2.
        self.assertAlmostEqual(float(he.interpolate_spectrum(f, np.array([x]))[0, 0]), 1.)

    def test_missing_and_negative_not_replaced_by_zero(self):
        for bad in (-1., math.nan, math.inf):
            f = np.ones((1, 8))
            f[0, 4] = bad
            with self.assertRaises(ValueError):
                self.response.calculate(f)
        with self.assertRaises(ValueError):
            self.response.calculate(np.ones((1, 11)))

    def test_primary_below_5_is_stopped_for_both_shields(self):
        al = he.AlphaTable("al")
        self.assertAlmostEqual(float(al.range(20.)), .05216, places=6)
        for rho in (2.5, 3.):
            self.assertLess(float(al.range(20.)), rho)
            np.testing.assert_array_equal(al.residual(np.geomspace(.001, 5, 100), rho), 0.)
        with self.assertRaises(ValueError):
            al.residual(np.array([1000.]), 3.)

    def test_alpha_energy_jacobian_known_flat(self):
        # Direct independent change of variables: the same particle integral
        # in alpha total energy and energy per nucleon, with dE_alpha=4 dE_nuc.
        en = np.linspace(5., 95.64, 1001)
        jn = np.full(en.shape, 2.3)
        measured_particles = np.trapezoid(jn, en)
        alpha_particles = np.trapezoid(jn/4, en*4)
        self.assertAlmostEqual(measured_particles, alpha_particles)
        self.assertAlmostEqual(measured_particles, 2.3*(95.64-5.))
        # Mutant: failing to divide differential alpha flux by four is caught.
        with self.assertRaises(AssertionError):
            np.testing.assert_allclose(measured_particles, np.trapezoid(jn, en*4), rtol=1e-12)

    def test_known_flat_response_normalization_and_particle_conservation(self):
        sigma0, flux0, bits = 2e-8, 2.3, 17
        def constant_response(let):
            return np.where(np.asarray(let) > 0, sigma0, 0.)
        with patch.object(he, "sigma_let", side_effect=constant_response):
            response = he.HeliumResponse(bits=bits, order=8, slope_step=.05)
        rates = response.calculate(np.full((1, 8), flux0))
        for name, rho in (("helium_3", 3.), ("helium_2p5", 2.5)):
            # Uniform incident measure has exactly this surviving width.
            low = float(response.al.inverse(rho+response.al.ranges[0])/4)
            incident = flux0*(95.64-5.)
            stopped = flux0*(low-5.)
            expected = bits*4*math.pi*sigma0*(incident-stopped)
            self.assertAlmostEqual(float(rates[name][0])/expected, 1., places=11)
            with self.assertRaises(AssertionError):
                np.testing.assert_allclose(rates[name][0], expected*4, rtol=1e-10)
            with self.assertRaises(AssertionError):
                np.testing.assert_allclose(rates[name][0], expected*4*math.pi, rtol=1e-10)

    def test_independent_dense_integration_and_zeros(self):
        # Separate dense trapezoidal integration uses its own interpolation,
        # Si stopping lookup and Weibull expression. No moment helper reused.
        inputs = np.array([[1.]*8, [0., 0., .1, .2, .1, 0., .01, .001],
                           [0., 0., 0., 0., 0., .02, 0., 0.]])
        rates = self.response.calculate(inputs)
        en = np.linspace(5., 95.64, 200001)
        al = np.genfromtxt(he.HERE/"inputs/nist_astar_al.csv", delimiter=",", names=True)
        si = np.genfromtxt(he.HERE/"inputs/nist_astar_si.csv", delimiter=",", names=True)
        r = np.exp(np.interp(np.log(4*en), np.log(al["energy_mev"]), np.log(al["csda_range_g_cm2"])))
        for rho, key in ((3., "helium_3"), (2.5, "helium_2p5")):
            keep = r-rho >= al["csda_range_g_cm2"][0]
            er = np.exp(np.interp(np.log(np.maximum(r-rho, al["csda_range_g_cm2"][0])),
                                 np.log(al["csda_range_g_cm2"]), np.log(al["energy_mev"])))
            let = np.exp(np.interp(np.log(er), np.log(si["energy_mev"]),
                                  np.log(si["electronic_stopping_mev_cm2_g"]))) / 1000
            sigma = np.zeros_like(let)
            active = keep & (let > .15)
            sigma[active] = 2.6e-7*(1-np.exp(-((let[active]-.15)/70)**1.2))
            for f, actual in zip(inputs, rates[key]):
                flux = np.zeros_like(en)
                for band in range(9):
                    edges = np.r_[5., he.ENERGY, 95.64]
                    low, high = edges[band:band+2]
                    mask = (en >= low) & (en <= high)
                    j = min(max(band-1, 0), 6)
                    t = np.log(en[mask]/he.ENERGY[j])/np.log(he.ENERGY[j+1]/he.ENERGY[j])
                    if f[j] > 0 and f[j+1] > 0:
                        flux[mask] = np.exp((1-t)*np.log(f[j])+t*np.log(f[j+1]))
                    else:
                        flux[mask] = np.maximum((1-t)*f[j]+t*f[j+1], 0.)
                expected = np.trapezoid(flux*sigma, en)*19922944*4*math.pi
                np.testing.assert_allclose(actual, expected, rtol=7e-5, atol=1e-15)

    def test_tail_is_conditional_not_upper_and_subkeV_is_disclosed(self):
        meta = self.response.metadata()
        self.assertEqual(meta["minimum_residual_energy_keV"], 1.)
        self.assertIsNone(meta["tail_above_250"])
        self.assertIsNone(meta["Z_ge_3_rate"])
        self.assertIn("not", meta["status"])
        rates = self.response.calculate(np.ones((1, 8)))
        for key in ("helium_3", "helium_2p5"):
            self.assertGreaterEqual(rates[key+"_tail250"][0], rates[key][0])

    def test_stream_api_header_identity_and_alignment_on_two_rows(self):
        with small_fixture_directory() as temp:
            root = Path(temp)
            package, source, cache = root/"package", root/"source", root/"cache"
            for p in (package/"inputs", package/"outputs", source):
                p.mkdir(parents=True)
            raw = ("Date Time F1 F2 F3 F4 F5 F6 F7 F8\n"
                   "2000-01-01 00:00:00,1,1,1,1,1,1,1,1\n"
                   "2000-01-01 00:05:00,0,0,0,0,0,0,0,0\n").encode("ascii")
            ref = {"records": 2, "numerically_complete": True,
                   "first_bin_start": "2000-01-01T00:00:00", "end_exclusive": "2000-01-01T00:10:00",
                   "sha256": hashlib.sha256(raw).hexdigest()}
            (source/"SEPEM_He_reference.txt").write_bytes(raw)
            audit = {"reference_series": {"SEPEM_H_reference.txt": ref, "SEPEM_He_reference.txt": ref}}
            (package/"outputs/input_audit.json").write_text(json.dumps(audit))
            (package/"config.json").write_text(json.dumps({"words": 524288, "protected_bits_per_word": 38}))
            (package/"inputs/astar_manifest.json").write_bytes((he.HERE/"inputs/astar_manifest.json").read_bytes())
            with patch.object(he, "HERE", package), patch.object(he, "HeliumResponse", return_value=self.response):
                result = he.compute_helium(source, cache, 2)
                expected = self.response.calculate(np.array([[1.]*8, [0.]*8]))
                for key, values in result["arrays"].items():
                    np.testing.assert_allclose(values, expected[key], rtol=0, atol=0)
                    # Close mappings explicitly on Windows before temp cleanup.
                    values._mmap.close()
                self.assertEqual(result["metadata"]["zeros_by_channel"], [1]*8)
                with self.assertRaises(ValueError):
                    he.compute_helium(source, cache, 3)


if __name__ == "__main__":
    unittest.main()
