<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n = getContext('i18n');

	import Spinner from '$lib/components/common/Spinner.svelte';
	import { createInvitation, listMyInvitations, revokeInvitation, deleteInvitation } from '$lib/apis/invitations';
	import type { InvitationResponse } from '$lib/apis/invitations';

	export let managedGroups = [];

	let invitations: InvitationResponse[] = [];
	let loading = false;
	let showCreateForm = false;

	// Create form state
	let selectedGroupId = '';
	let maxUses = null;
	let expiresInHours = null;
	let note = '';
	let creating = false;

	const loadInvitations = async () => {
		try {
			loading = true;
			const result = await listMyInvitations(localStorage.token);
			if (result) {
				invitations = result;
			}
		} catch (error) {
			console.error('Error loading invitations:', error);
			toast.error($i18n.t('Error loading invitations'));
		} finally {
			loading = false;
		}
	};

	const handleCreate = async () => {
		if (!selectedGroupId) {
			toast.error($i18n.t('Please select a group'));
			return;
		}

		try {
			creating = true;
			const data = {
				group_id: selectedGroupId,
				max_uses: maxUses || undefined,
				expires_in_hours: expiresInHours || undefined,
				note: note || undefined
			};

			const result = await createInvitation(localStorage.token, data);
			if (result) {
				toast.success($i18n.t('Invitation link created successfully'));
				showCreateForm = false;
				resetForm();
				await loadInvitations();
			}
		} catch (error) {
			console.error('Error creating invitation:', error);
			toast.error($i18n.t('Error creating invitation'));
		} finally {
			creating = false;
		}
	};

	const handleRevoke = async (invitationId: string) => {
		try {
			const result = await revokeInvitation(localStorage.token, invitationId);
			if (result && result.success) {
				toast.success($i18n.t('Invitation revoked successfully'));
				await loadInvitations();
			}
		} catch (error) {
			console.error('Error revoking invitation:', error);
			toast.error($i18n.t('Error revoking invitation'));
		}
	};

	const handleDelete = async (invitationId: string) => {
		if (!confirm($i18n.t('Are you sure you want to permanently delete this invitation?'))) {
			return;
		}

		try {
			const result = await deleteInvitation(localStorage.token, invitationId);
			if (result && result.success) {
				toast.success($i18n.t('Invitation deleted successfully'));
				await loadInvitations();
			}
		} catch (error) {
			console.error('Error deleting invitation:', error);
			toast.error($i18n.t('Error deleting invitation'));
		}
	};

	const copyToClipboard = (text: string) => {
		navigator.clipboard.writeText(text);
		toast.success($i18n.t('Copied to clipboard'));
	};

	const resetForm = () => {
		selectedGroupId = managedGroups.length > 0 ? managedGroups[0].id : '';
		maxUses = null;
		expiresInHours = null;
		note = '';
	};

	const formatDate = (timestamp: number | null) => {
		if (!timestamp) return $i18n.t('Never');
		return new Date(timestamp * 1000).toLocaleString();
	};

	const isExpired = (invitation: InvitationResponse) => {
		if (invitation.status !== 'active') return true;
		if (invitation.expires_at && invitation.expires_at < Date.now() / 1000) return true;
		if (invitation.max_uses && invitation.current_uses >= invitation.max_uses) return true;
		return false;
	};

	onMount(() => {
		if (managedGroups.length > 0) {
			selectedGroupId = managedGroups[0].id;
		}
		loadInvitations();
	});
</script>

<div class="space-y-4">
	<!-- Create Button -->
	<div class="flex justify-between items-center">
		<h2 class="text-lg font-medium text-gray-900 dark:text-gray-100">
			{$i18n.t('Invitation Links')}
		</h2>
		<button
			on:click={() => (showCreateForm = !showCreateForm)}
			class="px-4 py-2 bg-fixxit-primary hover:bg-fixxit-primary-hover text-white rounded-lg text-sm font-medium transition"
		>
			{showCreateForm ? $i18n.t('Cancel') : $i18n.t('Create Invitation')}
		</button>
	</div>

	<!-- Create Form -->
	{#if showCreateForm}
		<div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800">
			<h3 class="font-medium text-gray-900 dark:text-gray-100 mb-4">
				{$i18n.t('Create New Invitation Link')}
			</h3>

			<div class="space-y-4">
				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Group')} <span class="text-red-500">*</span>
					</label>
					<select
						bind:value={selectedGroupId}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					>
						{#each managedGroups as group}
							<option value={group.id}>{group.name}</option>
						{/each}
					</select>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Max Uses')} <span class="text-xs text-gray-500">({$i18n.t('Optional')})</span>
						</label>
						<input
							type="number"
							bind:value={maxUses}
							min="1"
							placeholder={$i18n.t('Unlimited')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							{$i18n.t('Expires In (Hours)')} <span class="text-xs text-gray-500">({$i18n.t('Optional')})</span>
						</label>
						<input
							type="number"
							bind:value={expiresInHours}
							min="1"
							placeholder={$i18n.t('Never expires')}
							class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
						/>
					</div>
				</div>

				<div>
					<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
						{$i18n.t('Note')} <span class="text-xs text-gray-500">({$i18n.t('Optional')})</span>
					</label>
					<input
						type="text"
						bind:value={note}
						placeholder={$i18n.t('e.g., New hire onboarding')}
						class="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2"
					/>
				</div>

				<button
					on:click={handleCreate}
					disabled={creating}
					class="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition"
				>
					{creating ? $i18n.t('Creating...') : $i18n.t('Generate Link')}
				</button>
			</div>
		</div>
	{/if}

	<!-- Invitations List -->
	{#if loading}
		<div class="flex justify-center py-8">
			<Spinner className="size-6" />
		</div>
	{:else if invitations.length === 0}
		<div class="text-center py-12">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke-width="1.5"
				stroke="currentColor"
				class="size-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244"
				/>
			</svg>
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
				{$i18n.t('No Invitation Links')}
			</h3>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				{$i18n.t('Create your first invitation link to start inviting users')}
			</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each invitations as invitation}
				<div
					class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 {isExpired(invitation) ? 'opacity-60' : ''}"
				>
					<div class="flex items-start justify-between mb-3">
						<div>
							<div class="flex items-center gap-2 mb-1">
								<span class="font-medium text-gray-900 dark:text-gray-100">
									{invitation.group_name}
								</span>
								<span
									class="px-2 py-0.5 text-xs rounded {invitation.status === 'active'
										? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
										: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}"
								>
									{invitation.status}
								</span>
							</div>
							{#if invitation.note}
								<p class="text-sm text-gray-600 dark:text-gray-400">{invitation.note}</p>
							{/if}
						</div>

						<div class="flex items-center gap-2">
							{#if invitation.status === 'active' && !isExpired(invitation)}
								<button
									on:click={() => handleRevoke(invitation.id)}
									class="px-3 py-1 text-sm text-orange-600 hover:text-orange-700 dark:text-orange-400"
								>
									{$i18n.t('Revoke')}
								</button>
							{/if}
							<button
								on:click={() => handleDelete(invitation.id)}
								class="px-3 py-1 text-sm text-red-600 hover:text-red-700 dark:text-red-400"
							>
								{$i18n.t('Delete')}
							</button>
						</div>
					</div>

					<!-- Invitation URL -->
					<div class="flex items-center gap-2 mb-3">
						<input
							type="text"
							value={invitation.invitation_url}
							readonly
							class="flex-1 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded font-mono"
						/>
						<button
							on:click={() => copyToClipboard(invitation.invitation_url)}
							class="px-3 py-2 bg-fixxit-primary hover:bg-fixxit-primary-hover text-white rounded text-sm font-medium transition"
						>
							{$i18n.t('Copy')}
						</button>
					</div>

					<!-- Stats -->
					<div class="flex items-center gap-6 text-sm text-gray-600 dark:text-gray-400">
						<div>
							<span class="font-medium">{$i18n.t('Uses')}:</span>
							{invitation.current_uses}
							{#if invitation.max_uses}
								/ {invitation.max_uses}
							{:else}
								/ {$i18n.t('Unlimited')}
							{/if}
						</div>
						<div>
							<span class="font-medium">{$i18n.t('Expires')}:</span>
							{formatDate(invitation.expires_at)}
						</div>
						<div>
							<span class="font-medium">{$i18n.t('Created')}:</span>
							{formatDate(invitation.created_at)}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
