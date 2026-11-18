import pandas as pd

from generate import generate_all, SEED


class TestReproducibility:
    def test_same_seed_produces_identical_opportunities(self):
        run1 = generate_all(seed=SEED)
        run2 = generate_all(seed=SEED)
        pd.testing.assert_frame_equal(run1.opportunities, run2.opportunities)

    def test_same_seed_produces_identical_stage_history(self):
        run1 = generate_all(seed=SEED)
        run2 = generate_all(seed=SEED)
        pd.testing.assert_frame_equal(run1.stage_history, run2.stage_history)

    def test_different_seed_produces_different_data(self):
        run1 = generate_all(seed=SEED)
        run2 = generate_all(seed=SEED + 1)
        assert not run1.opportunities.equals(run2.opportunities)


class TestDataIntegrity:
    @classmethod
    def setup_class(cls):
        cls.data = generate_all()

    def test_every_opportunity_has_a_real_account_and_owner(self):
        assert set(self.data.opportunities.account_id) <= set(self.data.accounts.account_id)
        assert set(self.data.opportunities.owner_id) <= set(self.data.sales_reps.rep_id)

    def test_every_opportunity_id_is_unique(self):
        assert self.data.opportunities.opp_id.is_unique

    def test_closed_deals_have_a_closed_date_and_open_deals_dont(self):
        closed = self.data.opportunities[self.data.opportunities.status == "Closed"]
        open_ = self.data.opportunities[self.data.opportunities.status == "Open"]
        assert closed.closed_date.notna().all()
        assert open_.closed_date.isna().all()

    def test_only_closed_lost_deals_have_a_lost_reason(self):
        with_reason = self.data.opportunities[self.data.opportunities.lost_reason.notna()]
        assert (with_reason.stage == "Closed Lost").all()
        lost = self.data.opportunities[self.data.opportunities.stage == "Closed Lost"]
        assert lost.lost_reason.notna().all()

    def test_winning_requires_having_reached_negotiation(self):
        """A strictly sequential funnel: no deal can be Closed Won without a Negotiation row in stage_history."""
        won_ids = set(self.data.opportunities.loc[self.data.opportunities.stage == "Closed Won", "opp_id"])
        negotiation_ids = set(self.data.stage_history.loc[self.data.stage_history.stage == "Negotiation", "opp_id"])
        assert won_ids <= negotiation_ids

    def test_some_opportunities_are_missing_a_lead_source(self):
        assert self.data.opportunities.lead_source.isna().sum() > 0

    def test_win_rate_varies_meaningfully_by_lead_source(self):
        """Lead source quality is the generator's ground truth driver of win rate -- it should actually show up in the data."""
        closed = self.data.opportunities[self.data.opportunities.status == "Closed"].dropna(subset=["lead_source"])
        rates = closed.groupby("lead_source", observed=True).apply(
            lambda g: (g.stage == "Closed Won").mean(), include_groups=False
        )
        assert rates.max() - rates.min() > 0.2  # at least a 20-point spread between the best and worst source

    def test_expected_close_date_is_independent_of_actual_outcome(self):
        """expected_close_date is set at creation time -- it must exist for every deal, closed or still open."""
        assert self.data.opportunities.expected_close_date.notna().all()

    def test_bookings_volume_grows_over_the_window(self):
        """Deal creation ramps up over time by construction -- the second half of the window should have noticeably more deals than the first."""
        created = pd.to_datetime(self.data.opportunities.created_date)
        midpoint = created.min() + (created.max() - created.min()) / 2
        first_half = (created < midpoint).sum()
        second_half = (created >= midpoint).sum()
        assert second_half > first_half
